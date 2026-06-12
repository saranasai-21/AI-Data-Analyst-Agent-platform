import React, { useEffect, useRef, useState } from 'react';
import { Streamlit, withStreamlitConnection, ComponentProps } from 'streamlit-component-lib';
import { fabric } from 'fabric';
import { Lock, Unlock, Type, Image as ImageIcon, Trash2, Layout, Settings } from 'lucide-react';

const SLIDE_WIDTH = 1600;
const SLIDE_HEIGHT = 900;

const PptEditor = ({ args }: ComponentProps) => {
  const { presentation_state } = args || {};
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [canvas, setCanvas] = useState<fabric.Canvas | null>(null);
  const [slides, setSlides] = useState<any[]>(presentation_state?.slides || []);
  const [activeSlideIdx, setActiveSlideIdx] = useState(0);
  const [isLocked, setIsLocked] = useState(false);
  const [selectedObj, setSelectedObj] = useState<fabric.Object | null>(null);
  const [scale, setScale] = useState(0.4);

  const lastSentStateRef = useRef<string>('');
  const activeSlideIdxRef = useRef(activeSlideIdx);
  const slidesRef = useRef(slides);

  useEffect(() => {
    activeSlideIdxRef.current = activeSlideIdx;
  }, [activeSlideIdx]);

  useEffect(() => {
    slidesRef.current = slides;
  }, [slides]);

  // Set Streamlit component frame height
  useEffect(() => {
    Streamlit.setFrameHeight(850);
  });

  // Calculate viewport scale fitting for the 1600x900 canvas
  const handleResize = () => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const containerW = rect.width - 48; // spacing padding
    const containerH = rect.height - 48;
    
    const scaleX = containerW / SLIDE_WIDTH;
    const scaleY = containerH / SLIDE_HEIGHT;
    const newScale = Math.min(scaleX, scaleY, 0.95); // max 95% scale to prevent edge overflows
    setScale(newScale);
  };

  useEffect(() => {
    window.addEventListener('resize', handleResize);
    setTimeout(handleResize, 100);
    return () => window.removeEventListener('resize', handleResize);
  }, [slides, activeSlideIdx]);

  // Sync state from Streamlit if it changes externally
  useEffect(() => {
    if (presentation_state?.slides) {
      const stateStr = JSON.stringify(presentation_state.slides);
      if (stateStr !== lastSentStateRef.current) {
        setSlides(presentation_state.slides);
        if (canvas) {
          loadSlide(activeSlideIdx, presentation_state.slides);
        }
      }
    }
  }, [presentation_state, canvas, activeSlideIdx]);

  // Helper to render mock chart visually
  const renderMockChart = (x: number, y: number, w: number, h: number, chartData: any) => {
    const objects: fabric.Object[] = [];
    
    // Background card
    const bg = new fabric.Rect({
      left: x,
      top: y,
      width: w,
      height: h,
      fill: '#f8fafc',
      stroke: '#cbd5e1',
      strokeWidth: 2,
      rx: 12,
      ry: 12
    });
    objects.push(bg);
    
    // Chart Title
    const title = new fabric.Text(chartData?.title || 'Data Trend Analysis', {
      left: x + 30,
      top: y + 25,
      fontSize: 24,
      fontFamily: 'Arial',
      fontWeight: 'bold',
      fill: '#1e293b'
    });
    objects.push(title);
    
    // Axes
    const xAxis = new fabric.Line([x + 60, y + h - 80, x + w - 40, y + h - 80], {
      stroke: '#94a3b8',
      strokeWidth: 3
    });
    const yAxis = new fabric.Line([x + 60, y + 80, x + 60, y + h - 80], {
      stroke: '#94a3b8',
      strokeWidth: 3
    });
    objects.push(xAxis, yAxis);
    
    // Draw 4 beautiful vertical columns
    const barColors = ['#0f766e', '#4f46e5', '#d97706', '#059669'];
    const barLabels = ['Q1', 'Q2', 'Q3', 'Q4'];
    const barValues = [0.45, 0.75, 0.60, 0.90]; // proportions
    
    const chartHeight = h - 180;
    const chartWidth = w - 140;
    const barWidth = Math.min(60, (chartWidth / 4) * 0.5);
    const spacing = (chartWidth - barWidth * 4) / 5;
    
    for (let i = 0; i < 4; i++) {
      const barHeight = chartHeight * barValues[i];
      const barLeft = x + 70 + spacing + i * (barWidth + spacing);
      const barTop = y + h - 80 - barHeight;
      
      const bar = new fabric.Rect({
        left: barLeft,
        top: barTop,
        width: barWidth,
        height: barHeight,
        fill: barColors[i],
        rx: 6,
        ry: 6
      });
      
      const label = new fabric.Text(barLabels[i], {
        left: barLeft + barWidth / 2,
        top: y + h - 60,
        fontSize: 16,
        fontFamily: 'Arial',
        fill: '#64748b',
        originX: 'center'
      });
      
      objects.push(bar, label);
    }
    
    const group = new fabric.Group(objects, {
      left: x,
      top: y,
      selectable: !isLocked,
      evented: !isLocked
    });
    (group as any).elementType = 'chart';
    (group as any).chartData = chartData;
    return group;
  };

  // Helper to render mock table visually
  const renderMockTable = (x: number, y: number, w: number, h: number, tableData: any) => {
    const objects: fabric.Object[] = [];
    
    const rows = 4;
    const cols = 3;
    const cellW = w / cols;
    const cellH = h / rows;
    
    const defaultHeaders = ['Metric', 'Benchmark', 'Current Performance'];
    const defaultRows = [
      ['Data Completeness', '90.0%', '98.4%'],
      ['Processing Latency', '< 500ms', '342ms'],
      ['Query Accuracy', '99.5%', '99.9%']
    ];
    
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cellLeft = x + c * cellW;
        const cellTop = y + r * cellH;
        
        const cellBg = new fabric.Rect({
          left: cellLeft,
          top: cellTop,
          width: cellW,
          height: cellH,
          fill: r === 0 ? '#1e293b' : (r % 2 === 1 ? '#ffffff' : '#f8fafc'),
          stroke: '#cbd5e1',
          strokeWidth: 1.5
        });
        
        const cellTextStr = r === 0 
          ? (tableData?.headers?.[c] || defaultHeaders[c])
          : (tableData?.rows?.[r - 1]?.[c] || defaultRows[r - 1]?.[c] || '-');
          
        const cellText = new fabric.Text(cellTextStr, {
          left: cellLeft + cellW / 2,
          top: cellTop + cellH / 2,
          fontSize: r === 0 ? 18 : 16,
          fontFamily: 'Arial',
          fontWeight: r === 0 ? 'bold' : 'normal',
          fill: r === 0 ? '#ffffff' : '#334155',
          originX: 'center',
          originY: 'center'
        });
        
        objects.push(cellBg, cellText);
      }
    }
    
    const group = new fabric.Group(objects, {
      left: x,
      top: y,
      selectable: !isLocked,
      evented: !isLocked
    });
    (group as any).elementType = 'table';
    (group as any).tableData = tableData;
    return group;
  };

  const loadSlide = (idx: number, currentSlides = slides) => {
    if (!canvas) return;
    const slide = currentSlides[idx];
    if (!slide) return;
    canvas.clear();
    canvas.setBackgroundColor('#ffffff', () => {});
    
    const elements = slide.elements || [];
    
    elements.forEach((elem: any) => {
      // Resolve dual coordinates: support both (x, y, w, h) and (left, top, width, height)
      const x = elem.x !== undefined ? elem.x : (elem.left !== undefined ? elem.left : 100);
      const y = elem.y !== undefined ? elem.y : (elem.top !== undefined ? elem.top : 100);
      const w = elem.w !== undefined ? elem.w : (elem.width !== undefined ? elem.width : 500);
      const h = elem.h !== undefined ? elem.h : (elem.height !== undefined ? elem.height : 150);
      
      let fObj: fabric.Object | null = null;
      const isReadonly = slide.layout === 'visual_analysis';

      if (elem.type === 'title') {
        fObj = new fabric.Textbox(elem.content || elem.text || 'Slide Title', {
          left: x,
          top: y,
          width: w,
          fontSize: elem.fontSize || 54,
          fontFamily: 'Arial',
          fill: elem.fill || '#1e293b',
          fontWeight: 'bold',
          editable: !isLocked && !isReadonly,
          selectable: !isLocked,
          evented: !isLocked,
        });
      } else if (elem.type === 'text') {
        fObj = new fabric.Textbox(elem.content || elem.text || 'Double click to edit text', {
          left: x,
          top: y,
          width: w,
          fontSize: elem.fontSize || 28,
          fontFamily: 'Arial',
          fill: elem.fill || '#334155',
          editable: !isLocked && !isReadonly,
          selectable: !isLocked,
          evented: !isLocked,
        });
      } else if (elem.type === 'bullets') {
        const bulletText = Array.isArray(elem.items) 
          ? elem.items.map((item: string) => `•  ${item}`).join('\n')
          : (elem.content || elem.text || '').split('\n').map((line: string) => line.trim().startsWith('•') ? line : `•  ${line}`).join('\n');

        fObj = new fabric.Textbox(bulletText, {
          left: x,
          top: y,
          width: w,
          fontSize: elem.fontSize || 24,
          fontFamily: 'Arial',
          fill: elem.fill || '#475569',
          lineHeight: 1.3,
          editable: !isLocked && !isReadonly,
          selectable: !isLocked,
          evented: !isLocked,
        });
      } else if (elem.type === 'image') {
        const imgUrl = elem.src || 'https://images.unsplash.com/photo-1542744094-3a31f103e35f?w=800';
        fabric.Image.fromURL(imgUrl, (img) => {
          img.set({
            left: x,
            top: y,
            width: w,
            height: h,
            selectable: !isLocked,
            evented: !isLocked,
          });
          img.scaleToWidth(w);
          if (img.getScaledHeight() > h) {
            img.scaleToHeight(h);
          }
          img.setCoords();
          (img as any).elementType = 'image';
          (img as any).src = imgUrl;
          canvas.add(img);
          canvas.renderAll();
        }, { crossOrigin: 'anonymous' });
        return;
      } else if (elem.type === 'chart') {
        const group = renderMockChart(x, y, w, h, elem.chart_data);
        canvas.add(group);
        canvas.renderAll();
        return;
      } else if (elem.type === 'table') {
        const group = renderMockTable(x, y, w, h, elem.table_data);
        canvas.add(group);
        canvas.renderAll();
        return;
      } else {
        // Fallback textbox for structural compatibility
        fObj = new fabric.Textbox(elem.text || elem.content || '', {
          left: x,
          top: y,
          width: w,
          fontSize: elem.fontSize || 24,
          fontFamily: 'Arial',
          fill: elem.fill || '#333333',
          editable: !isLocked && !isReadonly,
          selectable: !isLocked,
          evented: !isLocked,
        });
      }
      
      if (fObj) {
        (fObj as any).elementType = elem.type || 'text';
        fObj.setControlsVisibility({ mtr: !isLocked });
        canvas.add(fObj);
      }
    });
    
    canvas.renderAll();
  };

  const saveCanvasToState = (c: fabric.Canvas, idx: number) => {
    if (idx < 0 || idx >= slidesRef.current.length) return;
    const updatedSlides = JSON.parse(JSON.stringify(slidesRef.current));
    const objects = c.getObjects();
    
    const elements = objects.map(obj => {
      const type = (obj as any).elementType || 'text';
      const x = Math.round(obj.left || 0);
      const y = Math.round(obj.top || 0);
      const w = Math.round(obj.width ? obj.width * (obj.scaleX || 1) : 0);
      const h = Math.round(obj.height ? obj.height * (obj.scaleY || 1) : 0);
      
      if (type === 'title') {
        const textObj = obj as fabric.Textbox;
        return {
          type: 'title',
          content: textObj.text,
          x, y, w, h,
          fontSize: textObj.fontSize,
          fill: textObj.fill
        };
      } else if (type === 'text') {
        const textObj = obj as fabric.Textbox;
        return {
          type: 'text',
          content: textObj.text,
          x, y, w, h,
          fontSize: textObj.fontSize,
          fill: textObj.fill
        };
      } else if (type === 'bullets') {
        const textObj = obj as fabric.Textbox;
        const items = textObj.text?.split('\n').map(line => line.replace(/^•\s*/, '')) || [];
        return {
          type: 'bullets',
          items: items,
          x, y, w, h,
          fontSize: textObj.fontSize,
          fill: textObj.fill
        };
      } else if (type === 'image') {
        const imgObj = obj as any;
        return {
          type: 'image',
          src: imgObj.src || '',
          x, y, w, h
        };
      } else if (type === 'chart') {
        const chartObj = obj as any;
        return {
          type: 'chart',
          chart_data: chartObj.chartData || {},
          x, y, w, h
        };
      } else if (type === 'table') {
        const tableObj = obj as any;
        return {
          type: 'table',
          table_data: tableObj.tableData || {},
          x, y, w, h
        };
      }
      
      return {
        type: 'text',
        content: (obj as any).text || '',
        x, y, w, h
      };
    });
    
    updatedSlides[idx].elements = elements;
    setSlides(updatedSlides);
    
    const stateStr = JSON.stringify(updatedSlides);
    lastSentStateRef.current = stateStr;
    Streamlit.setComponentValue({ slides: updatedSlides });
  };

  useEffect(() => {
    if (canvasRef.current && !canvas) {
      const c = new fabric.Canvas(canvasRef.current, {
        width: SLIDE_WIDTH,
        height: SLIDE_HEIGHT,
        backgroundColor: '#ffffff',
        preserveObjectStacking: true,
      });
      
      const handleSelection = () => {
        setSelectedObj(c.getActiveObject());
      };
      
      c.on('selection:created', handleSelection);
      c.on('selection:updated', handleSelection);
      c.on('selection:cleared', () => setSelectedObj(null));
      
      c.on('object:moving', handleSelection);
      c.on('object:scaling', handleSelection);
      c.on('object:resizing', handleSelection);

      c.on('object:modified', () => {
        saveCanvasToState(c, activeSlideIdxRef.current);
        setSelectedObj(c.getActiveObject());
      });
      
      setCanvas(c);
    }
    
    return () => {
      if (canvas) {
        canvas.dispose();
      }
    };
  }, [canvasRef]);

  // Load active slide when index changes
  useEffect(() => {
    if (!canvas || slides.length === 0) return;
    loadSlide(activeSlideIdx, slides);
  }, [activeSlideIdx, canvas]);

  // Keybindings listener: Delete & Ctrl+D to duplicate
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!canvas) return;
      const activeObj = canvas.getActiveObject();
      if (!activeObj) return;

      const isEditing = (activeObj as any).isEditing;
      if (isEditing) return;

      if (e.key === 'Delete' || e.key === 'Backspace') {
        canvas.remove(activeObj);
        canvas.discardActiveObject();
        canvas.renderAll();
        saveCanvasToState(canvas, activeSlideIdxRef.current);
        setSelectedObj(null);
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        activeObj.clone((cloned: fabric.Object) => {
          cloned.set({
            left: (cloned.left || 0) + 30,
            top: (cloned.top || 0) + 30,
            evented: true
          });
          
          if (cloned.type === 'activeSelection') {
            (cloned as any).canvas = canvas;
            (cloned as any).forEachObject((obj: fabric.Object) => {
              canvas.add(obj);
            });
            canvas.setActiveObject(cloned);
          } else {
            canvas.add(cloned);
            canvas.setActiveObject(cloned);
          }
          
          canvas.renderAll();
          saveCanvasToState(canvas, activeSlideIdxRef.current);
        });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [canvas]);

  const handleAddText = () => {
    if (!canvas || isLocked) return;
    const text = new fabric.Textbox('Double click to edit text', {
      left: 100,
      top: 100,
      width: 400,
      fontSize: 28,
      fontFamily: 'Arial',
      fill: '#334155'
    });
    (text as any).elementType = 'text';
    canvas.add(text);
    canvas.setActiveObject(text);
    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdxRef.current);
  };

  const handleAddImage = () => {
    if (!canvas || isLocked) return;
    const url = prompt('Enter Image URL:', 'https://images.unsplash.com/photo-1542744094-3a31f103e35f?w=800');
    if (!url) return;
    
    fabric.Image.fromURL(url, (img) => {
      img.set({
        left: 100,
        top: 100,
        width: 400,
        height: 300,
        selectable: !isLocked,
        evented: !isLocked
      });
      img.scaleToWidth(400);
      img.setCoords();
      (img as any).elementType = 'image';
      (img as any).src = url;
      canvas.add(img);
      canvas.setActiveObject(img);
      canvas.renderAll();
      saveCanvasToState(canvas, activeSlideIdxRef.current);
    }, { crossOrigin: 'anonymous' });
  };

  const handleDeleteElement = () => {
    if (!canvas || !selectedObj || isLocked) return;
    canvas.remove(selectedObj);
    setSelectedObj(null);
    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdxRef.current);
  };

  const updateSelectedProperty = (property: string, value: any) => {
    if (!canvas || !selectedObj) return;
    
    const obj = selectedObj as any;
    if (property === 'text') {
      obj.set('text', value);
    } else if (property === 'fontSize') {
      obj.set('fontSize', parseInt(value) || 12);
    } else if (property === 'fill') {
      obj.set('fill', value);
    } else if (property === 'left') {
      obj.set('left', parseFloat(value) || 0);
    } else if (property === 'top') {
      obj.set('top', parseFloat(value) || 0);
    } else if (property === 'width') {
      obj.set('width', parseFloat(value) || 50);
      obj.scaleX = 1; 
    } else if (property === 'height') {
      obj.set('height', parseFloat(value) || 50);
      obj.scaleY = 1;
    }
    
    selectedObj.setCoords();
    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdxRef.current);
  };

  if (!slides || slides.length === 0) {
    return (
      <div className="flex h-[800px] w-full bg-[#09090b] rounded-xl border border-white/10 items-center justify-center flex-col text-zinc-100 shadow-2xl relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-900/20 via-[#09090b]/0 to-[#09090b] pointer-events-none"></div>
        <div className="relative z-10 flex flex-col items-center">
          <ImageIcon className="w-16 h-16 text-zinc-600 mb-4 drop-shadow-lg" />
          <h3 className="text-xl font-semibold tracking-tight">No slides to preview</h3>
          <p className="text-zinc-400 mt-2">Generate presentation to preview slides</p>
        </div>
      </div>
    );
  }

  const isTextObj = selectedObj && (selectedObj.type === 'textbox' || selectedObj.type === 'i-text');

  return (
    <div className="flex h-[800px] w-full bg-[#09090b] rounded-xl overflow-hidden border border-white/10 text-zinc-100 select-none shadow-2xl font-sans">
      {/* Sidebar - Slide Thumbnails (250px) */}
      <div className="w-[250px] min-w-[250px] bg-[#18181b]/80 backdrop-blur-xl border-r border-white/5 flex flex-col overflow-y-auto z-10">
        <div className="px-5 py-4 border-b border-white/5 font-bold text-zinc-200 flex justify-between items-center text-xs tracking-wider uppercase">
          <span>Slides Preview</span>
          <span className="text-[10px] font-bold px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded-full border border-indigo-500/30">{slides.length}</span>
        </div>
        <div className="p-4 space-y-4">
          {slides.map((slide, idx) => (
            <React.Fragment key={idx}>
              <div 
                onClick={() => setActiveSlideIdx(idx)}
                className={`p-3 rounded-xl cursor-pointer border transition-all duration-200 group ${activeSlideIdx === idx ? 'border-indigo-500/50 bg-indigo-500/10 shadow-[0_0_15px_rgba(99,102,241,0.15)] scale-[1.02]' : 'border-transparent hover:bg-white/5 hover:border-white/10'}`}
              >
                <div className={`text-[10px] font-bold mb-1.5 transition-colors ${activeSlideIdx === idx ? 'text-indigo-400' : 'text-zinc-500 group-hover:text-zinc-400'}`}>SLIDE {idx + 1}</div>
                <div className={`text-sm font-semibold truncate transition-colors ${activeSlideIdx === idx ? 'text-zinc-100' : 'text-zinc-300 group-hover:text-zinc-200'}`}>{slide.title || 'Untitled Slide'}</div>
                <div className="text-xs text-zinc-500 mt-1.5 capitalize font-medium">{slide.layout?.replace('_', ' ')}</div>
              </div>
              {idx < slides.length - 1 && (
                <div className="border-t border-white/5 my-2 mx-2" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Main Canvas Editor Area (Flex centered) */}
      <div className="flex-1 flex flex-col relative z-0">
        {/* Toolbar */}
        <div className="h-16 bg-[#18181b]/80 backdrop-blur-xl border-b border-white/5 flex items-center px-6 justify-between z-10 shadow-sm">
          <div className="flex items-center space-x-3">
            <button 
              onClick={handleAddText}
              disabled={isLocked}
              className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 text-zinc-200 flex items-center text-xs font-semibold transition-all border border-white/5 hover:border-white/10 hover:shadow-md"
            >
              <Type className="w-4 h-4 mr-2" /> Add Text
            </button>
            <button 
              onClick={handleAddImage}
              disabled={isLocked}
              className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 text-zinc-200 flex items-center text-xs font-semibold transition-all border border-white/5 hover:border-white/10 hover:shadow-md"
            >
              <ImageIcon className="w-4 h-4 mr-2" /> Add Image
            </button>
            <div className="w-px h-6 bg-white/10 mx-2"></div>
            <button 
              onClick={handleDeleteElement}
              disabled={!selectedObj || isLocked}
              className="px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 disabled:opacity-30 text-red-400 flex items-center text-xs font-semibold transition-all border border-red-500/20 hover:border-red-500/30 hover:shadow-[0_0_10px_rgba(239,68,68,0.2)]"
            >
              <Trash2 className="w-4 h-4 mr-2" /> Delete
            </button>
          </div>
          
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => {
                const newLock = !isLocked;
                setIsLocked(newLock);
                if (canvas) {
                  canvas.getObjects().forEach(obj => {
                    obj.selectable = !newLock;
                    obj.evented = !newLock;
                  });
                  canvas.discardActiveObject();
                  canvas.renderAll();
                }
              }}
              className={`px-4 py-2 rounded-lg flex items-center text-xs font-semibold transition-all border ${isLocked ? 'bg-amber-500/20 text-amber-300 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.15)]' : 'bg-white/5 hover:bg-white/10 text-zinc-200 border-white/5 hover:border-white/10'}`}
            >
              {isLocked ? <Lock className="w-4 h-4 mr-2" /> : <Unlock className="w-4 h-4 mr-2" />}
              {isLocked ? 'Locked Layout' : 'Unlock Layout'}
            </button>
          </div>
        </div>

        {/* Viewport Canvas container */}
        <div ref={containerRef} className="flex-1 bg-[#09090b] flex items-center justify-center p-6 overflow-hidden relative shadow-inner">
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '32px 32px' }}></div>
          <div 
            className="shadow-[0_20px_50px_rgba(0,0,0,0.5)] bg-white absolute transition-transform duration-75 ring-1 ring-white/10" 
            style={{ 
              width: SLIDE_WIDTH, 
              height: SLIDE_HEIGHT, 
              transform: `scale(${scale})`, 
              transformOrigin: 'center center' 
            }}
          >
            <canvas ref={canvasRef} />
            {slides[activeSlideIdx]?.layout === 'visual_analysis' && (
               <div className="absolute inset-0 bg-zinc-900/40 flex items-center justify-center pointer-events-none backdrop-blur-[2px]">
                 <div className="bg-[#18181b]/95 text-zinc-100 border border-white/10 px-8 py-4 rounded-2xl shadow-2xl text-xl font-bold tracking-tight">
                   Chart Analytics Canvas (Read Only)
                 </div>
               </div>
            )}
          </div>
        </div>
      </div>

      {/* Properties Panel (300px) */}
      <div className="w-[300px] min-w-[300px] bg-[#18181b]/80 backdrop-blur-xl border-l border-white/5 flex flex-col z-10">
        <div className="px-5 py-4 border-b border-white/5 font-bold text-zinc-200 flex items-center text-xs tracking-wider uppercase">
          <Settings className="w-4 h-4 mr-2 text-indigo-400" />
          <span>Properties Panel</span>
        </div>
        
        {selectedObj ? (
          <div className="p-5 flex-1 overflow-y-auto space-y-6">
            {/* Position and Size */}
            <div>
              <span className="text-[10px] font-bold text-zinc-500 tracking-wider block mb-3 uppercase">Layout Position</span>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-semibold text-zinc-400 block mb-1.5 uppercase">Pos X</label>
                  <input 
                    type="number" 
                    value={Math.round(selectedObj.left || 0)} 
                    onChange={(e) => updateSelectedProperty('left', e.target.value)}
                    className="w-full bg-[#09090b] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-zinc-400 block mb-1.5 uppercase">Pos Y</label>
                  <input 
                    type="number" 
                    value={Math.round(selectedObj.top || 0)} 
                    onChange={(e) => updateSelectedProperty('top', e.target.value)}
                    className="w-full bg-[#09090b] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-zinc-400 block mb-1.5 uppercase">Width</label>
                  <input 
                    type="number" 
                    value={Math.round(selectedObj.width ? selectedObj.width * (selectedObj.scaleX || 1) : 0)} 
                    onChange={(e) => updateSelectedProperty('width', e.target.value)}
                    className="w-full bg-[#09090b] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-zinc-400 block mb-1.5 uppercase">Height</label>
                  <input 
                    type="number" 
                    value={Math.round(selectedObj.height ? selectedObj.height * (selectedObj.scaleY || 1) : 0)} 
                    onChange={(e) => updateSelectedProperty('height', e.target.value)}
                    className="w-full bg-[#09090b] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner"
                  />
                </div>
              </div>
            </div>
            
            <div className="border-t border-white/5" />

            {/* Font Style edits if Text */}
            {isTextObj && (
              <div className="space-y-6">
                <div>
                  <span className="text-[10px] font-bold text-zinc-500 tracking-wider block mb-3 uppercase">Font Properties</span>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-[10px] font-semibold text-zinc-400 block mb-1.5 uppercase">Size</label>
                      <input 
                        type="number" 
                        value={(selectedObj as any).fontSize || 24} 
                        onChange={(e) => updateSelectedProperty('fontSize', e.target.value)}
                        className="w-full bg-[#09090b] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-semibold text-zinc-400 block mb-1.5 uppercase">Color</label>
                      <input 
                        type="color" 
                        value={selectedObj.fill as string || '#333333'} 
                        onChange={(e) => updateSelectedProperty('fill', e.target.value)}
                        className="w-full h-[34px] bg-[#09090b] border border-white/10 rounded-lg cursor-pointer p-0.5 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-zinc-500 tracking-wider block mb-3 uppercase">Edit Content</label>
                  <textarea 
                    value={(selectedObj as any).text || ''} 
                    onChange={(e) => updateSelectedProperty('text', e.target.value)}
                    className="w-full bg-[#09090b] border border-white/10 rounded-lg px-3 py-3 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 font-sans leading-relaxed transition-all shadow-inner resize-y"
                    rows={8}
                  />
                </div>
              </div>
            )}
            
            {/* Non-text elements details */}
            {!isTextObj && (
              <div>
                <span className="text-[10px] font-bold text-zinc-500 tracking-wider block mb-3 uppercase">Element Type</span>
                <div className="px-4 py-2.5 bg-indigo-500/10 rounded-lg text-sm font-semibold capitalize text-indigo-300 border border-indigo-500/20 shadow-inner">
                  {(selectedObj as any).elementType || selectedObj.type}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-8 flex-1 flex flex-col justify-center items-center text-center text-zinc-500 bg-[#09090b]/30">
            <Layout className="w-16 h-16 text-zinc-700 mb-4 drop-shadow-md" />
            <p className="text-xs leading-relaxed max-w-[200px]">
              Select an element on the canvas to configure its position, content, and styling parameters.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default withStreamlitConnection(PptEditor);
