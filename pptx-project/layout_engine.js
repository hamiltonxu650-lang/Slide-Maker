const PptxGenJS = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

const data_path = process.argv[2] || 'ocr_data.json';
const output_path = process.argv[3] || 'test_result_skill.pptx';
const resolvedDataPath = path.isAbsolute(data_path) ? data_path : path.resolve(process.cwd(), data_path);
const resolvedOutputPath = path.isAbsolute(output_path)
    ? output_path
    : path.resolve(__dirname, '..', output_path);

if (!fs.existsSync(resolvedDataPath)) {
    console.error("Input JSON not found.");
    process.exit(1);
}

const allSlidesData = JSON.parse(fs.readFileSync(resolvedDataPath, 'utf8'));

// Initialize pptxgen
let pres = new PptxGenJS();

// Basic Layout setup using first slide as reference
if (allSlidesData.length > 0) {
    const firstSlide = allSlidesData[0];
    pres.defineLayout({ 
        name:'Custom', 
        width: (firstSlide.width || 1024) / 96.0, 
        height: (firstSlide.height || 768) / 96.0 
    });
    pres.layout = 'Custom';
}

allSlidesData.forEach((slideData, idx) => {
    console.log(`Rendering Slide ${idx + 1}...`);
    let slide = pres.addSlide();
    const img_w = slideData.width || 1024;
    const img_h = slideData.height || 768;

    // Add clean background image
    if (slideData.background_image && fs.existsSync(slideData.background_image)) {
        let bgPath = slideData.background_image;
        let imgData = fs.readFileSync(bgPath);
        let base64 = imgData.toString('base64');
        let ext = path.extname(bgPath).replace('.', '').toLowerCase();
        if (ext === 'jpg') ext = 'jpeg';
        
        slide.addImage({
            data: `image/${ext};base64,${base64}`,
            x: 0, y: 0,
            w: img_w / 96.0,
            h: img_h / 96.0
        });
    }

    if (slideData.text_data) {
        let boxes = slideData.text_data;
        
        // Sort boxes top-to-bottom
        boxes.sort((a,b) => Math.min(...a.box.map(p=>p[1])) - Math.min(...b.box.map(p=>p[1])));
        
        // Strict 1:1 Layout Engine (No Clustering)
        // Disabling clustering guarantees text stays exactly where OCR found it.
        // It prevents PowerPoint from trying to line-wrap or auto-fit paragraphs,
        // which was causing the dreaded overlaps and out-of-bounds text.
        for (let b of boxes) {
            let b_x_min = Math.min(...b.box.map(p=>p[0]));
            let b_x_max = Math.max(...b.box.map(p=>p[0]));
            let b_y_min = Math.min(...b.box.map(p=>p[1]));
            let b_y_max = Math.max(...b.box.map(p=>p[1]));
            
            let w = b_x_max - b_x_min;
            let h = b_y_max - b_y_min;
            let boxScale = Number(b.pptx_box_scale || 1.5);
            let fontScale = Number(b.pptx_font_scale || 0.96);
            
            let r = Math.max(0, Math.min(255, b.color[0]));
            let g = Math.max(0, Math.min(255, b.color[1]));
            let b_c = Math.max(0, Math.min(255, b.color[2]));
            let colorHex = ((1 << 24) + (r << 16) + (g << 8) + b_c).toString(16).slice(1).toUpperCase();

            // Slightly inflate width and height bounding boxes in PPTX definition
            // so text absolutely never triggers soft-wrapping or clipping.
            let safe_w = (w * boxScale) / 96.0;
            let safe_h = (h * boxScale) / 96.0;

            slide.addText(b.text, {
                x: b_x_min / 96.0,
                y: b_y_min / 96.0,
                w: safe_w,
                h: safe_h,
                color: colorHex,
                fontSize: b.font_size * fontScale,
                valign: 'top', align: 'left',
                margin: 0,
                // CRITICAL: Disable wrapping to force text to strictly follow 1:1 coordinates
                wrap: false 
            });
        }
    }
});

pres.writeFile({ fileName: resolvedOutputPath }).then(() => {
    console.log(`Successfully generated multi-slide PPTX at ${resolvedOutputPath}`);
}).catch(err => {
    console.error("Error generating PPTX:", err);
});
