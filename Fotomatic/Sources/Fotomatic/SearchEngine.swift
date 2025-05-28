import Foundation
import SwiftSoup

struct SearchEngine: Identifiable {
    let id = UUID()
    let name: String
    let base: URL
    let queryParam: String

    func url(for term: String) -> URL? {
        guard var components = URLComponents(url: base, resolvingAgainstBaseURL: false) else { return nil }
        var queryItems = components.queryItems ?? []
        queryItems.append(URLQueryItem(name: queryParam, value: term))
        // Google image search requires tbm=isch and tbs=iar:w to get original images
        if name.lowercased() == "google" {
            queryItems.append(URLQueryItem(name: "tbm", value: "isch"))
            queryItems.append(URLQueryItem(name: "tbs", value: "iar:w"))
        }
        components.queryItems = queryItems
        return components.url
    }

    func fetch(_ term: String) async -> [URL] {
        guard let url = url(for: term) else { return [] }
        var request = URLRequest(url: url)
        request.setValue("Mozilla/5.0", forHTTPHeaderField: "User-Agent")

        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            guard let html = String(data: data, encoding: .utf8) else { return [] }
            let doc = try SwiftSoup.parse(html)
            let images = try doc.select("img").compactMap { try? $0.attr("src") }
            let urls = images.compactMap(URL.init)
            let unique = Array(Set(urls)).prefix(30)
            return Array(unique)
        } catch {
            return []
        }
    }
}

extension SearchEngine {
    static let google = SearchEngine(name: "Google", base: URL(string: "https://www.google.com/search")!, queryParam: "q")
    static let yandex = SearchEngine(name: "Yandex", base: URL(string: "https://yandex.com/images/search")!, queryParam: "text")
    static let pinterest = SearchEngine(name: "Pinterest", base: URL(string: "https://www.pinterest.com/search/pins/")!, queryParam: "q")
}
