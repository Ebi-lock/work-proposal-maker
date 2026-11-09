import Foundation
import PDFKit
import AppKit
let args = CommandLine.arguments
let doc = PDFDocument(url: URL(fileURLWithPath: args[1]))!
let outDir = args[2]
for i in 0..<doc.pageCount {
  let page = doc.page(at: i)!
  let r = page.bounds(for: .mediaBox)
  let scale: CGFloat = 1.0
  let img = page.thumbnail(of: NSSize(width: r.width*scale, height: r.height*scale), for: .mediaBox)
  let tiff = img.tiffRepresentation!
  let rep = NSBitmapImageRep(data: tiff)!
  let png = rep.representation(using: .png, properties: [:])!
  try! png.write(to: URL(fileURLWithPath: String(format: "%@/p%02d.png", outDir, i+1)))
}
