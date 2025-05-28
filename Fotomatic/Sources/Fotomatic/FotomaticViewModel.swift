import Foundation
import SwiftUI

@MainActor
final class FotomaticViewModel: ObservableObject {
    @Published var query = ""
    @Published var images: [URL] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let engines: [SearchEngine] = [.google, .yandex, .pinterest]

    func search() async {
        let term = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !term.isEmpty else { return }

        isLoading = true
        errorMessage = nil
        images = []

        await withTaskGroup(of: [URL].self) { group in
            for engine in engines {
                group.addTask {
                    await engine.fetch(term)
                }
            }

            var collected = Set<URL>()
            for await result in group {
                collected.formUnion(result)
            }
            images = Array(collected.prefix(60))
        }

        isLoading = false
        if images.isEmpty {
            errorMessage = "Nenhuma imagem encontrada."
        }
    }
}
