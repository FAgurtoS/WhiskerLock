from AppKit import (NSImage, NSBitmapImageRep, NSColor, NSBezierPath, NSString,
                    NSFont, NSFontAttributeName, NSGraphicsContext, NSMakeRect,
                    NSPNGFileType, NSDeviceRGBColorSpace)
S = 1024
rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
    None, S, S, 8, 4, True, False, NSDeviceRGBColorSpace, 0, 0)
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.setCurrentContext_(NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep))
NSColor.colorWithCalibratedRed_green_blue_alpha_(0.98, 0.78, 0.45, 1).setFill()
NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(40, 40, S-80, S-80), 200, 200).fill()
s = NSString.stringWithString_("🐱")
attrs = {NSFontAttributeName: NSFont.systemFontOfSize_(640)}
sz = s.sizeWithAttributes_(attrs)
s.drawAtPoint_withAttributes_(((S-sz.width)/2, (S-sz.height)/2), attrs)
NSGraphicsContext.restoreGraphicsState()
rep.representationUsingType_properties_(NSPNGFileType, None).writeToFile_atomically_("icon1024.png", True)
