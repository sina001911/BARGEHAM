export function getBadgeStyle(status: string) {
  switch (status) {
    case "ready":
      return "bg-green-100 text-green-700";
    case "processing":
      return "bg-yellow-100 text-yellow-700 animate-pulse";
    case "ocr_failed":
    case "error":
      return "bg-red-100 text-red-700";
    case "uploading":
      return "bg-blue-100 text-blue-700";
    default:
      return "bg-gray-100 text-gray-600";
  }
}
