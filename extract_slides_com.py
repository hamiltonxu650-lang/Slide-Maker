import os
import sys
import comtypes.client

def export_slides_via_com(pptx_path, out_dir):
    pptx_path = os.path.abspath(pptx_path)
    out_dir = os.path.abspath(out_dir)
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    print(f"Opening {pptx_path} via PowerPoint COM...")
    powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
    # powerpoint.Visible = True  # Required for some operations
    presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False)
    
    try:
        for i, slide in enumerate(presentation.Slides):
            print(f"Exporting Slide {i+1} as flattened image...")
            # FilterName=PNG
            output_file = os.path.join(out_dir, f"slide_{i+1:03d}.png")
            slide.Export(output_file, "PNG")
            print(f"  Saved {output_file}")
    finally:
        presentation.Close()
        # powerpoint.Quit() # Quitting might close the user's other PPTs, usually better to leave open or check if others are open

if __name__ == "__main__":
    pptx_file = sys.argv[1] if len(sys.argv) > 1 else "test/original.pptx"
    out_folder = "test/extracted_slides_com"
    export_slides_via_com(pptx_file, out_folder)
