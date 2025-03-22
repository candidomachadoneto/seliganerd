import sys, requests, base64, json, time, csv, os, feedparser, traceback
import google.generativeai as genai
from bs4 import BeautifulSoup
from datetime import datetime
from groq import Groq
import markdown

# Configurações iniciais
endpoint = 'seliganerd.com' #ou homolog.seliganerd.com
username = 'gemini'
password = '7^wY0n(!CX*Icyouj!0hueBp'
api_key_gemini = "AIzaSyCxo2wiK7NrtMLY7vvYg66qj8MjNCh7Cf0"
api_key_groq = "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"
csv_file = 'posted_news.csv'

# Configuração da API do Google Gemini
genai.configure(api_key=api_key_gemini)
model = genai.GenerativeModel('gemini-pro')

# Configuração da API do Groq
client = Groq(
    api_key=api_key_groq,
)

# Prompts de tradução
title_prompt = "Traduza o seguinte título de notícia para o português, buscando manter o estilo jornalístico e o tom do texto original. Adapte o título para que seja atraente e conciso para um público brasileiro, utilizando palavras-chave relevantes para SEO e mantendo o sentido original da mensagem. Limite em no máximo em 15 palavras."
excerpt_prompt = "Escreva uma gravata (lead) em português para a seguinte notícia, com base no primeiro parágrafo do texto. A gravata deve ser informativa, cativante e concisa, resumindo os principais pontos da notícia e incentivando o leitor a continuar lendo. Inclua palavras-chave relevantes para SEO e mantenha o tom e estilo do texto original:"
content_prompt = "Traduza o seguinte texto de notícia para o português, mantendo o estilo jornalístico, o tom e a estrutura do texto original. Adapte o texto para um público brasileiro, garantindo que a tradução seja fluida, natural e compreensível. Desconsidere tudo que vier em \"READ NEXT\" e a depois dele. Divida o resultado em dois subtitulos"

def build_auth_header():
    auth_str = f'{username}:{password}'
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    return {'Authorization': f'Basic {b64_auth_str}'}

def get_or_create_exact_tag_id(tag_name):
    auth_header = build_auth_header()
    # Indica que a busca pela tag exata está começando
    print(f"Buscando a tag com o nome exato: '{tag_name}'")
    
    # Buscar todas as tags que correspondem ao nome da tag
    url = f'https://{endpoint}/wp-json/wp/v2/tags?search={tag_name}'
    response = requests.get(url, headers=auth_header)
    if response.status_code == 200:
        tags = response.json()
        # Verifica se existe uma tag com o nome exatamente igual (respeitando capitalização e espaços)
        for tag in tags:
            if tag['name'] == tag_name:
                print(f"Tag encontrada: '{tag_name}' com ID: {tag['id']}")
                return tag['id']
    else:
        print(f"Falha ao buscar a tag '{tag_name}'. Código de status: {response.status_code}")

    # Se a tag não existir, crie-a
    print(f"Tag '{tag_name}' não encontrada. Criando nova tag.")
    create_url = f'https://{endpoint}/wp-json/wp/v2/tags'
    data = {'name': tag_name}
    response = requests.post(create_url, headers=auth_header, json=data)
    if response.status_code == 201:
        tag_id = response.json()['id']
        print(f"Tag '{tag_name}' criada com sucesso. ID: {tag_id}")
        return tag_id
    else:
        raise Exception(f"Falha ao criar a tag '{tag_name}'. Código de status: {response.status_code}")

def get_news_content(news_url):
    response = requests.get(news_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.text.replace('**', '')

        # Verifica o domínio do site
        if "thatparkplace.com" in news_url:
            content_div = soup.find('div', class_='et_pb_post_content')
            if content_div is None:
                raise Exception("Não foi possível encontrar a div com a classe 'et_pb_post_content' no site.")
            paragraphs = content_div.find_all('p')

            # Thumbnail específico para thatdarkplace.com
            thumbnail_span = soup.find('span', class_='et_pb_image_wrap')
            if thumbnail_span:
                thumbnail_img = thumbnail_span.find('img')
                if thumbnail_img:
                    thumbnail_url = thumbnail_img.get('src')
                else:
                    raise Exception("Não foi possível encontrar a imagem dentro do span com a classe 'et_pb_image_wrap'.")
            else:
                raise Exception("Não foi possível encontrar o span com a classe 'et_pb_image_wrap' no site.")
        else:  # Para outros sites, utiliza o <article>
            article = soup.find('article')
            if article is None:
                raise Exception("Não foi possível encontrar a tag <article> na página.")
            paragraphs = article.find_all('p')

            # Thumbnail genérico
            thumbnail_div = soup.find('figure', class_='tpd-post-thumbnail-container')
            if thumbnail_div:
                thumbnail_img = thumbnail_div.find('img')
                if thumbnail_img:
                    thumbnail_url = thumbnail_img.get('src')
                else:
                    raise Exception("Não foi possível encontrar a imagem dentro da figure com a classe 'tpd-post-thumbnail-container'.")
            else:
                raise Exception("Não foi possível encontrar a div com a classe 'tpd-post-thumbnail-container'.")

        # Localiza o primeiro parágrafo válido
        first_paragraph_index = next((i for i, p in enumerate(paragraphs) if p.text.strip()), None)
        if first_paragraph_index is None:
            raise Exception("Não foi possível encontrar um parágrafo válido no conteúdo.")

        excerpt = paragraphs[first_paragraph_index].text
        content = '\n'.join([p.text for p in paragraphs[first_paragraph_index:] if not p.text.startswith(("RELATED:", "NEXT: "))])

        return title, excerpt, content, thumbnail_url
    else:
        raise Exception(f"Falha ao obter o conteúdo da notícia. Status Code: {response.status_code}")



def translate_content(content, prompt="Por favor, traduza o seguinte texto para português:"):
    
    prompt = f"{prompt}\n\n{content}"
    response = ""
    
    try:
        response = model.generate_content(prompt)
        response = response.text
    except:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        response = chat_completion.choices[0].message.content
        
    return response

def text_to_html_paragraphs(text):
    style = "font-weight: 400;"
    lines = text.split('\n')
    lines = [markdown.markdown(line).strip() for line in lines if line.strip()]
    paragraphs = ''.join(f'<p style="{style}">{line}</p><br />' for line in lines)
    return paragraphs

def get_all_categories():
    
    auth_header = build_auth_header()
    url = f'https://{endpoint}/wp-json/wp/v2/categories?per_page=100'
    response = requests.get(url, headers=auth_header)
    if response.status_code == 200:
        categories = response.json()
        category_dict = {category['name'].lower(): category['id'] for category in categories}
        return category_dict
    else:
        raise Exception(f"Falha ao carregar categorias. Código de status: {response.status_code}")
    
def match_categories(text, categories):
    matched_categories = []
    text_lower = text.lower()
    for category_name, category_id in categories.items():
        if category_name in text_lower:
            print(f"Categoria encontrada no texto: '{category_name}'")
            matched_categories.append(category_id)
    return matched_categories

def download_image(image_url, local_image_path):
    response = requests.get(image_url, stream=True)
    if response.status_code == 200:
        with open(local_image_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print('Imagem baixada com sucesso:', local_image_path)
    else:
        print('Falha ao baixar a imagem. Código de status:', response.status_code)

def upload_image(image_path):
    auth_header = build_auth_header()
    with open(image_path, 'rb') as img_file:
        img_content = img_file.read()
    headers = {
        **auth_header,
        'Content-Disposition': 'attachment; filename=example.jpg',
        'Content-Type': 'image/jpeg'
    }
    media_upload_url = f'https://{endpoint}/wp-json/wp/v2/media'
    response = requests.post(media_upload_url, headers=headers, data=img_content)
    if response.status_code == 201:
        print("Imagem enviada com sucesso!")
        return response.json()['id']
    else:
        print("Falha ao enviar a imagem. Código de status:", response.status_code)
        return None

def post_to_wordpress(title, content, excerpt, image_url, category_ids):
    
    image_id = upload_image(image_url)
    auth_header = build_auth_header()
    url = f'https://{endpoint}/wp-json/wp/v2/posts'
    headers = {
        **auth_header,
        'Content-Type': 'application/json'
    }
    img_json = f"https://{endpoint}/wp-json/wp/v2/media/{image_id}"
    response_img_json = requests.get(img_json, headers=headers).json()
    img_tag = f'<img style="display:none" src="{response_img_json["guid"]["rendered"]}" />'
    content_with_img = img_tag + markdown.markdown(content)

    # Obtenha ou crie o ID da tag "destaque"
    tag_id = get_or_create_exact_tag_id("Destaque")

    data = {
        'title': title.replace('**', '').rstrip("."),
        'status': 'publish',
        'content': content_with_img,
        'excerpt': excerpt.replace('**', ''),
        'featured_media': image_id,
        'categories': category_ids, # Adiciona as categorias
        'tags': [tag_id]  # Adiciona a tag "destaque"
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        print("Post criado com sucesso!")
        print(json.dumps(response.json(), indent=4))
        return True
    else:
        print(json.dumps(response.json(), indent=4))
        raise Exception(f"Falha ao criar o post. Status Code: {response.status_code}")
    
def get_or_create_category_id(category_name):
    
    auth_header = build_auth_header()
    # Busca a categoria pelo nome
    url = f'https://{endpoint}/wp-json/wp/v2/categories?search={category_name}'
    response = requests.get(url, headers=auth_header)
    if response.status_code == 200:
        categories = response.json()
        for category in categories:
            if category['name'].lower() == category_name.lower():
                print(f"Categoria encontrada: '{category_name}' com ID: {category['id']}")
                return category['id']
    else:
        print(f"Falha ao buscar a categoria '{category_name}'. Código de status: {response.status_code}")

    # Se não encontrada, criar a categoria
    print(f"Categoria '{category_name}' não encontrada. Criando nova categoria.")
    create_url = f'https://{endpoint}/wp-json/wp/v2/categories'
    data = {'name': category_name}
    response = requests.post(create_url, headers=auth_header, json=data)
    if response.status_code == 201:
        category_id = response.json()['id']
        print(f"Categoria '{category_name}' criada com sucesso. ID: {category_id}")
        return category_id
    else:
        raise Exception(f"Falha ao criar a categoria '{category_name}'. Código de status: {response.status_code}")


def create_or_update_csv(news_url):
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, 'a', newline='') as csvfile:
        fieldnames = ['url', 'date', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        current_time = datetime.now()
        writer.writerow({'url': news_url, 'date': current_time.strftime('%Y-%m-%d'), 'time': current_time.strftime('%H:%M:%S')})

def is_url_posted(news_url):
    if not os.path.isfile(csv_file):
        return False
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['url'] == news_url:
                return True
    return False

# Carregar categorias no início do script
categories = get_all_categories()

def process_news_feed(feed_url):
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        news_url = entry.link
        if is_url_posted(news_url):
            print(f"URL já postada: {news_url}")
            continue
        print(f"Processando: {news_url}")
        try:
            title, excerpt, news_content, thumbnail_url = get_news_content(news_url)

            translated_title = translate_content(title, title_prompt)
            translated_excerpt = translate_content(excerpt, excerpt_prompt)
            translated_content = text_to_html_paragraphs(translate_content(news_content, content_prompt))

            local_image_path = "thumb.jpeg"
            download_image(thumbnail_url, local_image_path)

            # Determinar categorias
            matched_category_ids = match_categories(translated_title + " " + translated_content, categories)
            if not matched_category_ids:
                print("Nenhuma categoria correspondente encontrada. Usando categoria padrão.")
                matched_category_ids = [get_or_create_category_id("Notícias")]  # Categoria padrão

            if post_to_wordpress(translated_title, translated_content, translated_excerpt, local_image_path, matched_category_ids):
                create_or_update_csv(news_url)
                
        except Exception as e:
            print(f"Erro ao processar a notícia: {e}")
            traceback.print_exc()

# Lista de URLs de feeds RSS
rss_feed_urls = [
    'https://boundingintocomics.com/feed/',
    'https://thatparkplace.com/feed/'  # Novo feed adicionado
]

# Processar o feed RSS e postar as notícias no WordPress
# Processar cada feed da lista
for feed_url in rss_feed_urls:
    print(f"Processando feed: {feed_url}")
    try:
        process_news_feed(feed_url)
    except Exception as e:
        print(f"Erro ao processar o feed {feed_url}: {e}")
        traceback.print_exc()
