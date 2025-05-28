// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "Fotomatic",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "Fotomatic", targets: ["Fotomatic"])
    ],
    dependencies: [
        .package(url: "https://github.com/scinfu/SwiftSoup.git", from: "2.6.1")
    ],
    targets: [
        .executableTarget(
            name: "Fotomatic",
            dependencies: [
                .product(name: "SwiftSoup", package: "SwiftSoup")
            ],
            path: "Sources/Fotomatic"
        )
    ]
)
