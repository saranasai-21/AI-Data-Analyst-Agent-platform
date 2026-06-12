import React, { useEffect, useRef, useState } from 'react';
import { Streamlit, withStreamlitConnection, ComponentProps } from 'streamlit-component-lib';
import { fabric } from 'fabric';
import { Lock, Unlock, Type, Image as ImageIcon, Trash2, Copy, FileText, Download } from 'lucide-react';

const SLIDE_WIDTH = 960;
const SLIDE_HEIGHT = 540;

const PptEditor = ({ args }: ComponentProps) => {
  const { presentation_state } = args;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [canvas, setCanvas] = useState<fabric.Canvas | null>(null);
  const [slides, setSlides] = useState<any[]>(presentation_state?.slides || []);
  const [activeSlideIdx, setActiveSlideIdx] = useState(0);
  const [isLocked, setIsLocked] = useState(false);
  const [selectedObj, setSelectedObj] = useState<fabric.Object | null>(null);

  useEffect(() => {
    Streamlit.setFrameHeight(600);
  }, []);

  useEffect(() => {
    if (canvasRef.current && !canvas) {
      const c = new fabric.Canvas(canvasRef.current, {
        width: SLIDE_WIDTH,
        height: SLIDE_HEIGHT,
        backgroundColor: '#ffffff',
        preserveObjectStacking: true,
      });
      
      c.on('selection:created', (e) => setSelectedObj(e.selected?.[0] || null));
      c.on('selection:updated', (e) => setSelectedObj(e.selected?.[0] || null));
      c.on('selection:cleared', () => setSelectedObj(null));
      
      c.on('object:modified', () => {
        saveCanvasToState(c, activeSlideIdx);
      });
      
      setCanvas(c);
    }
    
    return () => {
      if (canvas) {
        canvas.dispose();
      }
    };
  }, [canvasRef]);

  // Load active slide
  useEffect(() => {
    if (!canvas || slides.length === 0) return;
    loadSlide(activeSlideIdx);
  }, [activeSlideIdx, canvas]);

  const loadSlide = (idx: number) => {
    if (!canvas) return;
    const slide = slides[idx];
    canvas.clear();
    canvas.setBackgroundColor('#ffffff', () => {});
    
    const elements = slide.elements || [];
    
    // Y tracker for auto layout if coordinates are missing
    let currentY = 50;

    elements.forEach((elem: any) => {
      let fObj: fabric.Object;
      const isReadonly = slide.layout === 'visual_analysis';

      if (elem.type === 'textbox' || elem.type === 'title' || elem.type === 'text') {
        fObj = new fabric.Textbox(elem.text || '', {
          left: elem.left || 50,
          top: elem.top || currentY,
          width: elem.width || (SLIDE_WIDTH - 100),
          fontSize: elem.fontSize || (elem.type === 'title' ? 44 : 24),
          fontFamily: 'Arial',
          fill: elem.fill || '#333333',
          fontWeight: elem.type === 'title' ? 'bold' : 'normal',
          editable: !isLocked && !isReadonly,
          selectable: !isLocked,
          evented: !isLocked,
        });
        currentY += (elem.height || 60) + 20;
      } else {
        // placeholder for shapes/images
        fObj = new fabric.Rect({
          left: elem.left || 50,
          top: elem.top || currentY,
          width: elem.width || 200,
          height: elem.height || 100,
          fill: '#e2e8f0',
          selectable: !isLocked,
          evented: !isLocked,
        });
        currentY += 120;
      }
      
      fObj.setControlsVisibility({
        mtr: !isLocked, // rotation
      });
      
      canvas.add(fObj);
    });
    
    canvas.renderAll();
  };

  const saveCanvasToState = (c: fabric.Canvas, idx: number) => {
    const updatedSlides = [...slides];
    const objects = c.getObjects();
    
    const elements = objects.map(obj => {
      if (obj.type === 'textbox' || obj.type === 'i-text') {
        const textObj = obj as fabric.Textbox;
        return {
          type: 'textbox',
          text: textObj.text,
          left: textObj.left,
          top: textObj.top,
          width: textObj.width,
          height: textObj.height,
          fontSize: textObj.fontSize,
          fill: textObj.fill
        };
      }
      return {
        type: 'shape',
        left: obj.left,
        top: obj.top,
        width: obj.width,
        height: obj.height
      };
    });
    
    updatedSlides[idx].elements = elements;
    setSlides(updatedSlides);
    
    // Send state back to Python
    Streamlit.setComponentValue({ slides: updatedSlides });
  };

  const handleAddText = () => {
    if (!canvas || isLocked) return;
    const text = new fabric.Textbox('New Text', {
      left: 100,
      top: 100,
      width: 400,
      fontSize: 24,
      fontFamily: 'Arial',
      fill: '#333333'
    });
    canvas.add(text);
    canvas.setActiveObject(text);
    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdx);
  };

  const handleDeleteElement = () => {
    if (!canvas || !selectedObj || isLocked) return;
    canvas.remove(selectedObj);
    setSelectedObj(null);
    saveCanvasToState(canvas, activeSlideIdx);
  };

  return (
    <div className="flex h-[600px] w-full bg-slate-100 rounded-lg overflow-hidden border border-slate-300">
      {/* Sidebar Thumbnails */}
      <div className="w-64 bg-slate-50 border-r border-slate-300 flex flex-col overflow-y-auto">
        <div className="p-4 bg-slate-200 border-b border-slate-300 font-bold text-slate-700 flex justify-between items-center">
          Slides
          <span className="text-xs font-normal text-slate-500">{slides.length}</span>
        </div>
        <div className="p-2 space-y-2">
          {slides.map((slide, idx) => (
            <div 
              key={idx}
              onClick={() => setActiveSlideIdx(idx)}
              className={`p-3 rounded cursor-pointer border-2 transition-all ${activeSlideIdx === idx ? 'border-blue-500 bg-white shadow-sm' : 'border-transparent hover:bg-slate-200'}`}
            >
              <div className="text-xs font-semibold text-slate-500 mb-1">Slide {idx + 1}</div>
              <div className="text-sm font-medium text-slate-800 truncate">{slide.title || 'Untitled'}</div>
              <div className="text-xs text-slate-400 mt-1">{slide.layout}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="h-14 bg-white border-b border-slate-300 flex items-center px-4 justify-between">
          <div className="flex items-center space-x-2">
            <button 
              onClick={handleAddText}
              disabled={isLocked}
              className="p-2 rounded hover:bg-slate-100 text-slate-700 disabled:opacity-50 flex items-center text-sm font-medium transition-colors"
            >
              <Type className="w-4 h-4 mr-2" /> Add Text
            </button>
            <button 
              disabled={isLocked}
              className="p-2 rounded hover:bg-slate-100 text-slate-700 disabled:opacity-50 flex items-center text-sm font-medium transition-colors"
            >
              <ImageIcon className="w-4 h-4 mr-2" /> Add Image
            </button>
            <div className="w-px h-6 bg-slate-300 mx-2"></div>
            <button 
              onClick={handleDeleteElement}
              disabled={!selectedObj || isLocked}
              className="p-2 rounded hover:bg-red-50 text-red-600 disabled:opacity-50 flex items-center text-sm font-medium transition-colors"
            >
              <Trash2 className="w-4 h-4 mr-2" /> Delete
            </button>
          </div>
          
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => {
                setIsLocked(!isLocked);
                if (canvas) {
                  canvas.getObjects().forEach(obj => {
                    obj.selectable = isLocked;
                    obj.evented = isLocked;
                  });
                  canvas.discardActiveObject();
                  canvas.renderAll();
                }
              }}
              className={`p-2 rounded flex items-center text-sm font-medium transition-colors ${isLocked ? 'bg-amber-100 text-amber-700' : 'hover:bg-slate-100 text-slate-700'}`}
            >
              {isLocked ? <Lock className="w-4 h-4 mr-2" /> : <Unlock className="w-4 h-4 mr-2" />}
              {isLocked ? 'Locked' : 'Unlocked'}
            </button>
          </div>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 bg-slate-200 flex items-center justify-center p-8 overflow-auto">
          <div className="shadow-lg bg-white relative" style={{ width: SLIDE_WIDTH, height: SLIDE_HEIGHT, transform: 'scale(0.85)', transformOrigin: 'center center' }}>
            <canvas ref={canvasRef} />
            {slides[activeSlideIdx]?.layout === 'visual_analysis' && (
               <div className="absolute inset-0 bg-slate-100/50 flex items-center justify-center pointer-events-none">
                 <div className="bg-white px-4 py-2 rounded-full shadow text-sm font-medium text-slate-500 border border-slate-200">
                   Chart Slide (Read Only)
                 </div>
               </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default withStreamlitConnection(PptEditor);
