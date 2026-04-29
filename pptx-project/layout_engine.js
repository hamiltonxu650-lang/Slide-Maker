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
const MAX_SLIDE_INCHES = 55.95;

function slideDpi(slideData) {
    const dpi = Number(slideData.canvas_dpi || 96);
    return Number.isFinite(dpi) && dpi > 0 ? dpi : 96;
}

function layoutSize(slideData) {
    const dpi = slideDpi(slideData);
    const imgW = slideData.width || 1024;
    const imgH = slideData.height || 768;
    const widthIn = imgW / dpi;
    const heightIn = imgH / dpi;
    const longestEdge = Math.max(widthIn, heightIn, 0.01);
    const coordinateScale = Math.min(1.0, MAX_SLIDE_INCHES / longestEdge);
    return {
        dpi,
        width: widthIn * coordinateScale,
        height: heightIn * coordinateScale,
        coordinateScale,
    };
}

// Initialize pptxgen
let pres = new PptxGenJS();

// Basic Layout setup using first slide as reference
if (allSlidesData.length > 0) {
    const firstSlide = allSlidesData[0];
    const firstLayout = layoutSize(firstSlide);
    pres.defineLayout({ 
        name:'Custom', 
        width: firstLayout.width,
        height: firstLayout.height,
    });
    pres.layout = 'Custom';
}

allSlidesData.forEach((slideData, idx) => {
    console.log(`Rendering Slide ${idx + 1}...`);

    const img_w = slideData.width || 1024;
    const img_h = slideData.height || 768;
    const slideLayout = layoutSize(slideData);
    const dpi = slideLayout.dpi;
    const coordinateScale = slideLayout.coordinateScale;

    // Adapt slide dimensions per slide
    const layoutName = `Slide_${idx + 1}`;
    pres.defineLayout({
        name: layoutName,
        width: slideLayout.width,
        height: slideLayout.height,
    });
    pres.layout = layoutName;

    let slide = pres.addSlide();

    // Add clean background image
    if (slideData.background_image && fs.existsSync(slideData.background_image)) {
        let bgPath = slideData.background_image;
        let imgData = fs.readFileSync(bgPath);
        let base64 = imgData.toString('base64');
        let ext = path.extname(bgPath).replace('.', '').toLowerCase();
        if (ext === 'jpg') ext = 'jpeg';

        slide.addImage({
            data: `data:image/${ext};base64,${base64}`,
            x: 0, y: 0,
            w: slideLayout.width,
            h: slideLayout.height,
        });
    }

    if (slideData.text_data) {
        let boxes = slideData.text_data;
        
        // Sort boxes top-to-bottom
        boxes.sort((a,b) => Math.min(...a.box.map(p=>p[1])) - Math.min(...b.box.map(p=>p[1])));
        
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

            let safe_w = (w * boxScale / dpi) * coordinateScale;
            let safe_h = (h * boxScale / dpi) * coordinateScale;

            slide.addText(b.text, {
                x: (b_x_min / dpi) * coordinateScale,
                y: (b_y_min / dpi) * coordinateScale,
                w: safe_w,
                h: safe_h,
                color: colorHex,
                fontSize: b.font_size * fontScale * coordinateScale,
                valign: 'top', align: 'left',
                margin: 0,
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
