import Foundation

enum TimeFilter: String, CaseIterable, Identifiable {
    case all       = "All time"
    case lastHour  = "Last hour"
    case last24h   = "Last 24h"
    case lastWeek  = "Last week"
    case lastMonth = "Last month"

    var id: String { rawValue }

    /// Predefined parameters for Google (`tbs`) and Bing (`qft`)
    var googleTbs: String? {
        switch self {
        case .all:       return nil
        case .lastHour:  return "qdr:h"
        case .last24h:   return "qdr:d"
        case .lastWeek:  return "qdr:w"
        case .lastMonth: return "qdr:m"
        }
    }

    var bingQft: String? {
        switch self {
        case .all:       return nil
        case .lastHour:  return "+filterui:age-lt24hr"
        case .last24h:   return "+filterui:age-lt24hr"
        case .lastWeek:  return "+filterui:age-lt7days"
        case .lastMonth: return "+filterui:age-lt30days"
        }
    }
}
