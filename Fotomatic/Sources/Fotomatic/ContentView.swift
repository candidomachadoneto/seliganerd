import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = FotomaticViewModel()

    private let columns = [GridItem(.adaptive(minimum: 200))]

    var body: some View {
        VStack {
            Text("Fotomatic")
                .font(.largeTitle)
                .padding(.top)

            HStack {
                TextField("Buscar imagens", text: $viewModel.query)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .onSubmit {
                        Task { await viewModel.search() }
                    }

                Button("Buscar") {
                    Task { await viewModel.search() }
                }
                .disabled(viewModel.query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            .padding()

            if viewModel.isLoading {
                ProgressView().padding()
            }

            ScrollView {
                LazyVGrid(columns: columns, spacing: 8) {
                    ForEach(viewModel.images, id: \.self) { url in
                        AsyncImage(url: url) { phase in
                            switch phase {
                            case .empty:
                                ZStack { Color.gray.opacity(0.3); ProgressView() }
                            case .success(let image):
                                image
                                    .resizable()
                                    .aspectRatio(contentMode: .fill)
                            case .failure:
                                ZStack { Color.gray }
                            @unknown default:
                                EmptyView()
                            }
                        }
                        .frame(height: 120)
                        .clipped()
                    }
                }
                .padding()
            }

            if let message = viewModel.errorMessage {
                Text(message)
                    .foregroundColor(.red)
                    .padding()
            }
        }
    }
}

#Preview {
    ContentView()
}
