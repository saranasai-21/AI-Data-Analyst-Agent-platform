import React, { useEffect, useRef, useState } from 'react';
import { Streamlit, withStreamlitConnection, ComponentProps } from 'streamlit-component-lib';
import { fabric } from 'fabric';
import {
  Lock, Unlock, Type, Image as ImageIcon, Trash2, Layout, Settings,
  List, Table as TableIcon, BarChart3, ZoomIn, ZoomOut, Maximize2,
  HelpCircle, ChevronLeft, ChevronRight, Download, Save, Undo2, Redo2, Square, Share2, Layers, Sparkles
} from 'lucide-react';

const SLIDE_WIDTH = 1600;
const SLIDE_HEIGHT = 900;

// Set global fabric selection handle styles for a Figma-like feel
fabric.Object.prototype.set({
  cornerColor: '#ffffff',
  cornerStrokeColor: '#8b5cf6', // Purple 500
  cornerSize: 12,
  cornerStyle: 'circle',
  transparentCorners: false,
  borderColor: '#8b5cf6',
  borderScaleFactor: 2,
  padding: 8,
});

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

  // Collapsible sidebars state
  const [isLeftBarOpen, setIsLeftBarOpen] = useState(true);
  const [isRightBarOpen, setIsRightBarOpen] = useState(true);
  
  // Transparency slider state
  const [showTransparencySlider, setShowTransparencySlider] = useState(false);
  const [currentOpacityVal, setCurrentOpacityVal] = useState(100);

  // Undo/Redo element history stacks
  const [undoStack, setUndoStack] = useState<any[]>([]);
  const [redoStack, setRedoStack] = useState<any[]>([]);

  const lastSentStateRef = useRef<string>('');
  const activeSlideIdxRef = useRef(activeSlideIdx);
  const slidesRef = useRef(slides);
  const currentLoadSlideIdxRef = useRef<number>(-1);

  useEffect(() => {
    activeSlideIdxRef.current = activeSlideIdx;
  }, [activeSlideIdx]);

  useEffect(() => {
    slidesRef.current = slides;
  }, [slides]);

  useEffect(() => {
    Streamlit.setFrameHeight(880);
  }, []);

  // Calculate default viewport scale
  const handleResize = () => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const padding = 64;
    const containerW = rect.width - padding;
    const containerH = rect.height - padding;

    const scaleX = containerW / SLIDE_WIDTH;
    const scaleY = containerH / SLIDE_HEIGHT;
    const newScale = Math.min(scaleX, scaleY, 0.95);
    setScale(Math.max(0.1, Number(newScale.toFixed(2))));
  };

  useEffect(() => {
    window.addEventListener('resize', handleResize);
    handleResize();
    const timer = setTimeout(handleResize, 100);
    return () => {
      window.removeEventListener('resize', handleResize);
      clearTimeout(timer);
    };
  }, [slides, activeSlideIdx, isLeftBarOpen, isRightBarOpen, selectedObj]);

  // Sync state externally from Streamlit
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

  // Render mock charts visually on canvas
  const renderMockChart = (x: number, y: number, w: number, h: number, chartData: any) => {
    const objects: fabric.Object[] = [];
    const bg = new fabric.Rect({
      left: x,
      top: y,
      width: w,
      height: h,
      fill: '#1e293b',
      stroke: '#334155',
      strokeWidth: 2,
      rx: 12,
      ry: 12
    });
    objects.push(bg);

    const title = new fabric.Text(chartData?.title || 'Data Trend Analysis', {
      left: x + 40,
      top: y + 35,
      fontSize: 26,
      fontFamily: 'Arial',
      fontWeight: 'bold',
      fill: '#f1f5f9'
    });
    objects.push(title);

    const xAxis = new fabric.Line([x + 80, y + h - 100, x + w - 50, y + h - 100], {
      stroke: '#475569',
      strokeWidth: 3
    });
    const yAxis = new fabric.Line([x + 80, y + 100, x + 80, y + h - 100], {
      stroke: '#475569',
      strokeWidth: 3
    });
    objects.push(xAxis, yAxis);

    const isMockup = chartData?.type === 'mockup_bar';
    const barColors = ['#06b6d4', '#8b5cf6', '#f59e0b', '#10b981'];
    const mockupColors = ['#5391e6', '#59b8eb', '#06b6d4', '#0284c7', '#7dd3fc'];
    
    const colorsToUse = isMockup ? mockupColors : barColors;
    const labelsToUse = isMockup ? ['Item 1', 'Item 2', 'Item 3', 'Item 4', 'Item 5'] : ['Q1', 'Q2', 'Q3', 'Q4'];
    const valuesToUse = isMockup ? [0.28, 0.40, 0.56, 0.72, 0.88] : [0.45, 0.75, 0.60, 0.90];
    const count = isMockup ? 5 : 4;

    const chartHeight = h - 220;
    const chartWidth = w - 180;
    const barWidth = Math.min(80, (chartWidth / count) * 0.5);
    const spacing = (chartWidth - barWidth * count) / (count + 1);

    for (let i = 0; i < count; i++) {
      const barHeight = chartHeight * valuesToUse[i];
      const barLeft = x + 100 + spacing + i * (barWidth + spacing);
      const barTop = y + h - 100 - barHeight;

      const bar = new fabric.Rect({
        left: barLeft,
        top: barTop,
        width: barWidth,
        height: barHeight,
        fill: colorsToUse[i],
        rx: 8,
        ry: 8
      });

      const label = new fabric.Text(labelsToUse[i], {
        left: barLeft + barWidth / 2,
        top: y + h - 75,
        fontSize: 18,
        fontFamily: 'Arial',
        fill: '#94a3b8',
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

  // Render mock tables visually on canvas
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
          fill: r === 0 ? '#1e293b' : (r % 2 === 1 ? '#0f172a' : '#1e293b'),
          stroke: '#334155',
          strokeWidth: 1.5
        });

        const cellTextStr = r === 0
          ? (tableData?.headers?.[c] || defaultHeaders[c])
          : (tableData?.rows?.[r - 1]?.[c] || defaultRows[r - 1]?.[c] || '-');

        const cellText = new fabric.Text(cellTextStr, {
          left: cellLeft + cellW / 2,
          top: cellTop + cellH / 2,
          fontSize: r === 0 ? 20 : 18,
          fontFamily: 'Arial',
          fontWeight: r === 0 ? 'bold' : 'normal',
          fill: '#f1f5f9',
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

    const mapFillColor = (fill: string | undefined, defaultColor: string) => {
      if (!fill) return defaultColor;
      const darkColors = ['#1e293b', '#0f172a', '#334155', '#475569', '#0f294a', '#0d0d0e', '#09090b', '#000000', 'black', 'rgba(15,23,42,1)', 'rgba(30,41,59,1)'];
      if (darkColors.includes(fill.toLowerCase())) {
        return '#ffffff';
      }
      return fill;
    };

    currentLoadSlideIdxRef.current = idx;
    canvas.clear();
    const bgGrad = new fabric.Gradient({
      type: 'radial',
      coords: {
        x1: 100,
        y1: 450,
        r1: 0,
        x2: 800,
        y2: 450,
        r2: 1200,
      },
      colorStops: [
        { offset: 0, color: '#2b215c' },
        { offset: 0.5, color: '#0f121b' },
        { offset: 1, color: '#0a0b0e' }
      ]
    });
    canvas.setBackgroundColor(bgGrad, () => {
      canvas.renderAll();
    });

    const elements = slide.elements || [];

    elements.forEach((elem: any) => {
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
          fill: mapFillColor(elem.fill, '#ffffff'),
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
          fill: mapFillColor(elem.fill, '#cbd5e1'),
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
          fill: mapFillColor(elem.fill, '#cbd5e1'),
          lineHeight: 1.3,
          editable: !isLocked && !isReadonly,
          selectable: !isLocked,
          evented: !isLocked,
        });
      } else if (elem.type === 'image') {
        const imgUrl = elem.src || 'https://images.unsplash.com/photo-1542744094-3a31f103e35f?w=800';
        fabric.Image.fromURL(imgUrl, (img) => {
          if (currentLoadSlideIdxRef.current !== idx) return;
          img.set({
            left: x,
            top: y,
            selectable: !isLocked,
            evented: !isLocked,
          });

          const scaleX = w / img.width!;
          const scaleY = h / img.height!;
          const scaleFactor = Math.min(scaleX, scaleY);

          img.set({
            scaleX: scaleFactor,
            scaleY: scaleFactor
          });
          img.setCoords();
          (img as any).elementType = 'image';
          (img as any).src = imgUrl;
          (img as any).chartKey = elem.chart_key || elem.chartKey || '';
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
      } else if (elem.type === 'shape') {
        fObj = new fabric.Rect({
          left: x,
          top: y,
          width: w,
          height: h,
          fill: elem.fill || '#e2e8f0',
          stroke: elem.isBackground ? undefined : '#cbd5e1',
          strokeWidth: elem.isBackground ? 0 : 2,
          rx: elem.isBackground ? 0 : 8,
          ry: elem.isBackground ? 0 : 8,
          selectable: !elem.isBackground && !isLocked,
          evented: !elem.isBackground && !isLocked,
          hoverCursor: elem.isBackground ? 'default' : undefined
        });
        (fObj as any).isBackground = elem.isBackground || false;
      } else {
        fObj = new fabric.Textbox(elem.text || elem.content || '', {
          left: x,
          top: y,
          width: w,
          fontSize: elem.fontSize || 24,
          fontFamily: 'Arial',
          fill: elem.fill || '#ffffff',
          editable: !isLocked && !isReadonly,
          selectable: !isLocked,
          evented: !isLocked,
        });
      }

      if (fObj) {
        (fObj as any).elementType = elem.type || 'text';
        fObj.set('opacity', elem.opacity !== undefined ? elem.opacity : 1.0);
        fObj.setControlsVisibility({ mtr: !isLocked });
        canvas.add(fObj);
        if ((fObj as any).isBackground) {
          canvas.sendToBack(fObj);
        }
      }
    });
    canvas.renderAll();
  };

  const serializeCanvasElements = (c: fabric.Canvas) => {
    const objects = c.getObjects();
    return objects.map(obj => {
      const type = (obj as any).elementType || 'text';
      const x = Math.round(obj.left || 0);
      const y = Math.round(obj.top || 0);
      const w = Math.round(obj.width ? obj.width * (obj.scaleX || 1) : 0);
      const h = Math.round(obj.height ? obj.height * (obj.scaleY || 1) : 0);
      const opacity = obj.opacity ?? 1.0;

      if (type === 'title') {
        const textObj = obj as fabric.Textbox;
        return {
          type: 'title',
          content: textObj.text,
          x, y, w, h,
          fontSize: textObj.fontSize,
          fill: textObj.fill,
          opacity
        };
      } else if (type === 'text') {
        const textObj = obj as fabric.Textbox;
        return {
          type: 'text',
          content: textObj.text,
          x, y, w, h,
          fontSize: textObj.fontSize,
          fill: textObj.fill,
          opacity
        };
      } else if (type === 'bullets') {
        const textObj = obj as fabric.Textbox;
        const items = textObj.text?.split('\n').map(line => line.replace(/^•\s*/, '')) || [];
        return {
          type: 'bullets',
          items: items,
          x, y, w, h,
          fontSize: textObj.fontSize,
          fill: textObj.fill,
          opacity
        };
      } else if (type === 'image') {
        const imgObj = obj as any;
        return {
          type: 'image',
          src: imgObj.src || '',
          chart_key: imgObj.chartKey || '',
          x, y, w, h,
          opacity
        };
      } else if (type === 'chart') {
        const chartObj = obj as any;
        return {
          type: 'chart',
          chart_data: chartObj.chartData || {},
          x, y, w, h,
          opacity
        };
      } else if (type === 'table') {
        const tableObj = obj as any;
        return {
          type: 'table',
          table_data: tableObj.tableData || {},
          x, y, w, h,
          opacity
        };
      } else if (type === 'shape') {
        const shapeObj = obj as fabric.Rect;
        return {
          type: 'shape',
          x, y, w, h,
          fill: shapeObj.fill,
          isBackground: (shapeObj as any).isBackground || false,
          opacity
        };
      }
      return {
        type: 'text',
        content: (obj as any).text || '',
        x, y, w, h,
        opacity
      };
    });
  };

  const saveCanvasToState = (c: fabric.Canvas, idx: number, extraProperties = {}) => {
    if (idx < 0 || idx >= slidesRef.current.length) return;
    const updatedSlides = JSON.parse(JSON.stringify(slidesRef.current));
    const elements = serializeCanvasElements(c);

    updatedSlides[idx].elements = elements;
    setSlides(updatedSlides);

    const stateStr = JSON.stringify(updatedSlides);
    lastSentStateRef.current = stateStr;

    Streamlit.setComponentValue({
      slides: updatedSlides,
      ...extraProperties
    });
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
        // Track history before modification
        const currentElements = serializeCanvasElements(c);
        setUndoStack(prev => [...prev, currentElements]);
        setRedoStack([]); // clear redo on new action

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

  useEffect(() => {
    if (!canvas || slides.length === 0) return;
    loadSlide(activeSlideIdx, slides);
    // Clear undo/redo stacks when loading a new slide
    setUndoStack([]);
    setRedoStack([]);
  }, [activeSlideIdx, canvas]);

  // Keybindings delete/duplicate element
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!canvas) return;
      const activeObj = canvas.getActiveObject();
      if (!activeObj) return;

      const isEditing = (activeObj as any).isEditing;
      if (isEditing) return;

      if (e.key === 'Delete' || e.key === 'Backspace') {
        const currentElements = serializeCanvasElements(canvas);
        setUndoStack(prev => [...prev, currentElements]);

        canvas.remove(activeObj);
        canvas.discardActiveObject();
        canvas.renderAll();
        saveCanvasToState(canvas, activeSlideIdxRef.current);
        setSelectedObj(null);
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        const currentElements = serializeCanvasElements(canvas);
        setUndoStack(prev => [...prev, currentElements]);

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

  // Toolbar Element Creators
  const handleAddText = () => {
    if (!canvas || isLocked) return;
    const text = new fabric.Textbox('Double click to edit text', {
      left: 200,
      top: 200,
      width: 400,
      fontSize: 28,
      fontFamily: 'Arial',
      fill: '#ffffff'
    });
    (text as any).elementType = 'text';
    canvas.add(text);
    canvas.setActiveObject(text);
    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdxRef.current);
  };

  const handleAddBullets = () => {
    if (!canvas || isLocked) return;
    const bullets = new fabric.Textbox('•  First bullet item\n•  Second bullet item', {
      left: 200,
      top: 200,
      width: 500,
      fontSize: 24,
      fontFamily: 'Arial',
      fill: '#cbd5e1',
      lineHeight: 1.3
    });
    (bullets as any).elementType = 'bullets';
    canvas.add(bullets);
    canvas.setActiveObject(bullets);
    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdxRef.current);
  };

  const handleAddShape = () => {
    if (!canvas || isLocked) return;
    const rect = new fabric.Rect({
      left: 200,
      top: 200,
      width: 300,
      height: 200,
      fill: '#8b5cf6',
      stroke: '#7c3aed',
      strokeWidth: 2,
      rx: 12,
      ry: 12
    });
    (rect as any).elementType = 'shape';
    canvas.add(rect);
    canvas.setActiveObject(rect);
    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdxRef.current);
  };

  const handleAddImage = () => {
    if (!canvas || isLocked) return;
    const url = prompt('Enter Image URL:', 'https://images.unsplash.com/photo-1542744094-3a31f103e35f?w=800');
    if (!url) return;

    fabric.Image.fromURL(url, (img) => {
      img.set({
        left: 200,
        top: 200,
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

  const handleAddTable = () => {
    if (!canvas || isLocked) return;
    const tableData = {
      headers: ['Metric', 'Benchmark', 'Current'],
      rows: [
        ['Data completion', '90.0%', '98.4%'],
        ['Processing latency', '< 500ms', '342ms']
      ]
    };
    const group = renderMockTable(200, 200, 600, 180, tableData);
    canvas.add(group);
    canvas.setActiveObject(group);
    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdxRef.current);
  };

  const handleAddChart = () => {
    if (!canvas || isLocked) return;
    const chartData = { title: 'Business Performance Trend' };
    const group = renderMockChart(200, 200, 600, 360, chartData);
    canvas.add(group);
    canvas.setActiveObject(group);
    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdxRef.current);
  };

  const handleAddSlide = () => {
    const newSlide = {
      id: `slide_${Date.now()}`,
      layout: 'custom',
      title: `Slide ${slides.length + 1}`,
      elements: [
        {
          type: 'title',
          text: 'New Slide Title',
          x: 100,
          y: 80,
          w: 1400,
          h: 100,
          fontSize: 44,
          fill: '#ffffff'
        }
      ]
    };
    const updatedSlides = [...slides, newSlide];
    setSlides(updatedSlides);
    setActiveSlideIdx(updatedSlides.length - 1);

    // Save state back to streamlit component
    Streamlit.setComponentValue({ slides: updatedSlides });
  };

  const handleDeleteElement = () => {
    if (!canvas || !selectedObj || isLocked) return;
    const currentElements = serializeCanvasElements(canvas);
    setUndoStack(prev => [...prev, currentElements]);

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

  // Undo/Redo Handlers
  const handleUndo = () => {
    if (!canvas || undoStack.length === 0) return;
    const currentElements = serializeCanvasElements(canvas);
    setRedoStack(prev => [currentElements, ...prev]);

    const previousElements = undoStack[undoStack.length - 1];
    setUndoStack(prev => prev.slice(0, prev.length - 1));

    // Reload slide with previous elements
    const updatedSlides = JSON.parse(JSON.stringify(slides));
    updatedSlides[activeSlideIdx].elements = previousElements;
    setSlides(updatedSlides);
    loadSlide(activeSlideIdx, updatedSlides);

    // Save to Streamlit
    saveCanvasToState(canvas, activeSlideIdx);
  };

  const handleRedo = () => {
    if (!canvas || redoStack.length === 0) return;
    const currentElements = serializeCanvasElements(canvas);
    setUndoStack(prev => [...prev, currentElements]);

    const nextElements = redoStack[0];
    setRedoStack(prev => prev.slice(1));

    const updatedSlides = JSON.parse(JSON.stringify(slides));
    updatedSlides[activeSlideIdx].elements = nextElements;
    setSlides(updatedSlides);
    loadSlide(activeSlideIdx, updatedSlides);

    saveCanvasToState(canvas, activeSlideIdx);
  };

  // Header Actions
  const handleHeaderAction = (actionType: 'download' | 'save' | 'template') => {
    if (!canvas) return;
    saveCanvasToState(canvas, activeSlideIdx, { action: actionType });
  };

  const handleZoom = (type: 'in' | 'out' | 'set', val?: number) => {
    if (type === 'in') {
      setScale(prev => Math.min(prev + 0.1, 2.0));
    } else if (type === 'out') {
      setScale(prev => Math.max(prev - 0.1, 0.2));
    } else if (type === 'set' && val) {
      setScale(val);
    }
  };

  const BG_COLORS = [
    '#0f294a', '#1e293b', '#311b92', '#004d40', '#4a148c',
    '#880e4f', '#0f172a', '#1e1b4b', '#111827', '#022c22',
    '#3b0764', '#450a0a', '#172554', '#1e3a8a', '#134e4a'
  ];

  const handleTemplateReplacement = () => {
    if (!canvas) return;

    // Remove existing background elements
    const existingBg = canvas.getObjects().filter(obj => (obj as any).isBackground);
    existingBg.forEach(obj => canvas.remove(obj));

    const numColors = Math.floor(Math.random() * 3) + 1; // 1, 2, or 3
    const isVertical = Math.random() > 0.5;

    // Select random unique colors from BG_COLORS
    const colors: string[] = [];
    const availableColors = [...BG_COLORS];
    for (let i = 0; i < numColors; i++) {
      const idx = Math.floor(Math.random() * availableColors.length);
      colors.push(availableColors.splice(idx, 1)[0]);
    }

    if (numColors === 1) {
      const bg = new fabric.Rect({
        left: 0,
        top: 0,
        width: SLIDE_WIDTH,
        height: SLIDE_HEIGHT,
        fill: colors[0],
        selectable: false,
        evented: false,
        hoverCursor: 'default'
      });
      (bg as any).elementType = 'shape';
      (bg as any).isBackground = true;
      canvas.add(bg);
      canvas.sendToBack(bg);
    } else {
      for (let i = 0; i < numColors; i++) {
        let left = 0;
        let top = 0;
        let width = SLIDE_WIDTH;
        let height = SLIDE_HEIGHT;

        if (isVertical) {
          width = SLIDE_WIDTH / numColors;
          left = i * width;
        } else {
          height = SLIDE_HEIGHT / numColors;
          top = i * height;
        }

        const bg = new fabric.Rect({
          left,
          top,
          width,
          height,
          fill: colors[i],
          selectable: false,
          evented: false,
          hoverCursor: 'default'
        });
        (bg as any).elementType = 'shape';
        (bg as any).isBackground = true;
        canvas.add(bg);
        canvas.sendToBack(bg);
      }
    }

    canvas.renderAll();
    saveCanvasToState(canvas, activeSlideIdxRef.current);
  };

  const handleToggleTransparency = () => {
    setShowTransparencySlider(!showTransparencySlider);
    
    if (!showTransparencySlider && canvas) {
      const activeObj = canvas.getActiveObject();
      if (activeObj) {
        setCurrentOpacityVal(Math.round((activeObj.opacity ?? 1.0) * 100));
      } else {
        const bgObjects = canvas.getObjects().filter(obj => (obj as any).isBackground);
        if (bgObjects.length > 0) {
          setCurrentOpacityVal(Math.round((bgObjects[0].opacity ?? 1.0) * 100));
        }
      }
    }
  };

  const handleOpacityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    setCurrentOpacityVal(val);
    const nextOpacity = val / 100.0;
    
    if (!canvas) return;
    const activeObj = canvas.getActiveObject();
    if (activeObj) {
      activeObj.set('opacity', nextOpacity);
      canvas.renderAll();
      saveCanvasToState(canvas, activeSlideIdxRef.current);
      setSelectedObj({ ...selectedObj, opacity: nextOpacity } as any);
    } else {
      const bgObjects = canvas.getObjects().filter(obj => (obj as any).isBackground);
      if (bgObjects.length > 0) {
        bgObjects.forEach(obj => obj.set('opacity', nextOpacity));
        canvas.renderAll();
        saveCanvasToState(canvas, activeSlideIdxRef.current);
      }
    }
  };

  const renderMiniPreview = (slide: any) => {
    const isDark = slide.layout === 'title_slide' || slide.layout === 'conclusion_slide';
    const elements = slide.elements || [];

    return (
      <div className="w-full h-14 rounded-md border border-white/5 relative overflow-hidden transition-all duration-200 bg-[#0f294a]">
        {/* Background visual details based on layout */}
        {slide.layout === 'title_slide' && (
          <div className="absolute inset-0 flex flex-col justify-center items-center p-2 space-y-1">
            <div className="w-12 h-1 bg-indigo-400 rounded-sm"></div>
            <div className="w-8 h-0.5 bg-zinc-500 rounded-sm"></div>
          </div>
        )}
        {slide.layout === 'bullet_points' && (
          <div className="absolute inset-0 p-2 space-y-1">
            <div className="w-8 h-1 bg-zinc-400 rounded-sm mb-1"></div>
            <div className="w-12 h-0.5 bg-zinc-600 rounded-sm"></div>
            <div className="w-10 h-0.5 bg-zinc-600 rounded-sm"></div>
          </div>
        )}
        {slide.layout === 'visual_analysis' && (
          <div className="absolute inset-0 p-1.5 flex space-x-1.5">
            <div className="flex-1 space-y-0.5">
              <div className="w-5 h-1 bg-zinc-400 rounded-sm mb-1"></div>
              <div className="w-full h-0.5 bg-zinc-600 rounded-sm"></div>
              <div className="w-4/5 h-0.5 bg-zinc-600 rounded-sm"></div>
            </div>
            <div className="w-8 h-8 bg-indigo-500/20 border border-indigo-500/30 rounded flex items-center justify-center">
              <BarChart3 className="w-3 h-3 text-indigo-400" />
            </div>
          </div>
        )}
        {/* Generic or Custom elements rendering */}
        {slide.layout !== 'title_slide' && slide.layout !== 'bullet_points' && slide.layout !== 'visual_analysis' && (
          <div className="absolute inset-0 p-2 space-y-1">
            <div className="w-10 h-1 bg-zinc-400 rounded-sm mb-1"></div>
            <div className="flex flex-wrap gap-1">
              {elements.slice(0, 3).map((el: any, i: number) => {
                if (el.type === 'image' || el.type === 'chart') {
                  return <div key={i} className="w-4 h-3 bg-indigo-500/20 rounded border border-indigo-500/30"></div>;
                } else if (el.type === 'table') {
                  return <div key={i} className="w-4 h-3 bg-teal-500/20 rounded border border-teal-500/30"></div>;
                } else {
                  return <div key={i} className="w-6 h-0.5 bg-zinc-600 rounded-sm"></div>;
                }
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  const isTextObj = selectedObj && (selectedObj.type === 'textbox' || selectedObj.type === 'i-text');

  return (
    <div className="flex flex-col h-[800px] w-full bg-[#0d0d0e] rounded-2xl overflow-hidden border border-white/10 text-zinc-100 select-none shadow-2xl font-sans relative">

      {/* 1. Top Header Bar with download action */}
      <div className="h-[64px] bg-[#0d0d0e]/95 border-b border-white/[0.06] flex items-center justify-between px-6 z-25 relative shadow-md">
        {/* Left: Branding & Editor actions */}
        <div className="flex items-center space-x-4">
          <span className="text-xs font-black tracking-widest text-zinc-400 uppercase">SLIDE CREATOR</span>
          <div className="w-px h-4 bg-white/10"></div>
          
          {/* Quick edit tools: Undo, Redo, Add shapes, etc. */}
          <div className="flex items-center space-x-1.5">
            <button
              onClick={handleUndo}
              disabled={undoStack.length === 0}
              className="p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.08] disabled:opacity-20 text-zinc-400 hover:text-white transition-colors"
              title="Undo"
            >
              <Undo2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleRedo}
              disabled={redoStack.length === 0}
              className="p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.08] disabled:opacity-20 text-zinc-400 hover:text-white transition-colors"
              title="Redo"
            >
              <Redo2 className="w-4 h-4" />
            </button>
            <div className="w-px h-4 bg-white/10 mx-1"></div>
            <button
              onClick={handleAddText}
              disabled={isLocked}
              className="p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.08] text-zinc-400 hover:text-white transition-colors"
              title="Add Text"
            >
              <Type className="w-4 h-4" />
            </button>
            <button
              onClick={handleAddBullets}
              disabled={isLocked}
              className="p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.08] text-zinc-400 hover:text-white transition-colors"
              title="Add Bullets"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={handleAddShape}
              disabled={isLocked}
              className="p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.08] text-zinc-400 hover:text-white transition-colors"
              title="Add Shape"
            >
              <Square className="w-4 h-4" />
            </button>
            <button
              onClick={handleAddImage}
              disabled={isLocked}
              className="p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.08] text-zinc-400 hover:text-white transition-colors"
              title="Add Image"
            >
              <ImageIcon className="w-4 h-4" />
            </button>
            <button
              onClick={handleAddTable}
              disabled={isLocked}
              className="p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.08] disabled:opacity-20 text-zinc-400 hover:text-white transition-colors"
              title="Add Table"
            >
              <TableIcon className="w-4 h-4" />
            </button>
            <button
              onClick={handleAddChart}
              disabled={isLocked}
              className="p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.08] disabled:opacity-20 text-zinc-400 hover:text-white transition-colors"
              title="Add Chart"
            >
              <BarChart3 className="w-4 h-4" />
            </button>
          </div>

          <div className="w-px h-4 bg-white/10 mx-1"></div>
          {/* Colors & Templates */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleTemplateReplacement}
              className="px-2.5 py-1 rounded-lg bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 flex items-center text-[11px] font-semibold transition-all border border-indigo-500/20"
            >
              <Share2 className="w-3 h-3 mr-1" /> Style
            </button>
            <div className="relative flex items-center">
              <button
                onClick={handleToggleTransparency}
                className="px-2.5 py-1 rounded-lg bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-300 flex items-center text-[11px] font-semibold transition-all border border-indigo-500/20"
              >
                <Layers className="w-3 h-3 mr-1" /> Opacity
              </button>
              {showTransparencySlider && (
                <div className="absolute top-full mt-2 left-0 w-48 bg-[#161619] border border-indigo-500/20 p-3 rounded-lg shadow-xl z-50 flex flex-col space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-indigo-300 font-semibold">Opacity</span>
                    <span className="text-xs text-indigo-300">{currentOpacityVal}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="0" 
                    max="100" 
                    value={currentOpacityVal} 
                    onChange={handleOpacityChange}
                    className="w-full h-1 bg-indigo-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Customize text and Present Button */}
        <div className="flex items-center space-x-6">
          <span className="text-zinc-400 text-xs italic tracking-wide">Customize content and brand colour.</span>
          <button
            onClick={() => handleHeaderAction('download')}
            className="px-5 py-2.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] text-white flex items-center text-xs font-semibold tracking-wide transition-all border border-white/10 shadow-[0_4px_20px_rgba(0,0,0,0.3)] italic cursor-pointer"
          >
            Download and present <Sparkles className="w-3.5 h-3.5 ml-2 text-indigo-400" />
          </button>
        </div>
      </div>

      {/* 2. Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden relative">

        {/* Left Sidebar - slide navigator (collapsible) */}
        <div
          className={`h-full bg-[#131316]/95 border-r border-white/[0.06] flex flex-col transition-all duration-300 relative z-20 shadow-lg ${isLeftBarOpen ? 'w-[210px]' : 'w-0 border-r-0 overflow-hidden'
            }`}
        >
          <div className="p-3 border-b border-white/[0.06]">
            <button
              onClick={handleAddSlide}
              className="w-full py-1.5 rounded-lg border border-white/10 hover:border-indigo-500/50 bg-white/[0.02] hover:bg-indigo-500/10 text-zinc-300 hover:text-white text-xs font-bold transition-all"
            >
              + Add Slide
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-2 select-none">
            {slides.map((slide, idx) => (
              <div
                key={idx}
                onClick={() => setActiveSlideIdx(idx)}
                className={`p-2 mx-1.5 rounded-xl cursor-pointer border transition-all duration-200 group flex flex-col relative ${activeSlideIdx === idx
                    ? 'border-indigo-500/50 bg-indigo-500/10 shadow-[0_0_15px_rgba(99,102,241,0.15)] scale-[1.01]'
                    : 'border-transparent hover:bg-white/5 hover:border-white/10'
                  }`}
              >
                <div className="relative w-full">
                  {renderMiniPreview(slide)}
                  <div className="absolute bottom-1.5 left-1.5 bg-[#3b82f6] text-white text-[10px] font-bold w-4 h-4 rounded-sm flex items-center justify-center shadow-md">
                    {idx + 1}
                  </div>
                </div>
                <div className="text-xs font-semibold truncate text-zinc-300 mt-1.5 group-hover:text-zinc-200 pl-1">{slide.title || 'Untitled'}</div>
              </div>
            ))}
          </div>

          <div className="p-3 border-t border-white/[0.06]">
            <button className="w-full py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-extrabold shadow-md">
              Slide{activeSlideIdx + 1} / {slides.length}
            </button>
          </div>
        </div>

        {/* Left Toggle arrow tab */}
        <button
          onClick={() => setIsLeftBarOpen(!isLeftBarOpen)}
          className="absolute left-0 top-1/2 -translate-y-1/2 w-4 h-12 bg-[#131316] hover:bg-indigo-600/30 border border-white/10 hover:border-indigo-500 border-l-0 rounded-r-lg z-25 flex items-center justify-center text-zinc-500 hover:text-white transition-all shadow-md"
        >
          {isLeftBarOpen ? <ChevronLeft className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        </button>

        {/* Center Canvas Viewport - scrollable zoom viewport */}
        <div ref={containerRef} className="flex-1 bg-[#09090b] flex items-center justify-center p-8 overflow-auto relative">
          <div
            style={{
              padding: '16px',
              border: '2px dashed rgba(255, 255, 255, 0.15)',
              borderRadius: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <div
              style={{
                width: SLIDE_WIDTH * scale,
                height: SLIDE_HEIGHT * scale,
                position: 'relative'
              }}
              className="slide-canvas-shadow bg-white rounded-sm ring-1 ring-black/20"
            >
              <div
                style={{
                  width: SLIDE_WIDTH,
                  height: SLIDE_HEIGHT,
                  transform: `scale(${scale})`,
                  transformOrigin: 'top left',
                  position: 'absolute',
                  left: 0,
                  top: 0
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
        </div>

        {/* 3. Collapsible Right Properties Panel (sidebar layout, visible only on selection) */}
        {selectedObj && (
          <div className="w-[280px] h-full bg-[#161619]/95 border-l border-white/[0.06] flex flex-col z-20 shadow-lg relative animate-fade-in">
            <div className="px-4 py-3 bg-white/[0.02] border-b border-white/[0.06] flex items-center justify-between">
              <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider flex items-center">
                <Settings className="w-3.5 h-3.5 mr-1.5" /> Element Settings
              </span>
              <button
                onClick={() => {
                  if (canvas) {
                    canvas.discardActiveObject();
                    canvas.renderAll();
                    setSelectedObj(null);
                  }
                }}
                className="text-zinc-500 hover:text-zinc-300 text-xs font-bold font-sans"
              >
                ✕
              </button>
            </div>
            <div className="p-4 space-y-4 overflow-y-auto flex-1">

              {/* Positions */}
              <div>
                <label className="text-[9px] font-bold text-zinc-400 block mb-2 uppercase tracking-wider">Coordinates</label>
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-[#0c0c0d] border border-white/10 rounded-lg p-1.5 flex items-center">
                    <span className="text-[10px] text-zinc-500 font-mono w-4">X</span>
                    <input
                      type="number"
                      value={Math.round(selectedObj.left || 0)}
                      onChange={(e) => updateSelectedProperty('left', e.target.value)}
                      className="bg-transparent border-0 w-full text-xs text-zinc-200 focus:outline-none p-0 ml-1 font-mono"
                    />
                  </div>
                  <div className="bg-[#0c0c0d] border border-white/10 rounded-lg p-1.5 flex items-center">
                    <span className="text-[10px] text-zinc-500 font-mono w-4">Y</span>
                    <input
                      type="number"
                      value={Math.round(selectedObj.top || 0)}
                      onChange={(e) => updateSelectedProperty('top', e.target.value)}
                      className="bg-transparent border-0 w-full text-xs text-zinc-200 focus:outline-none p-0 ml-1 font-mono"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <div className="bg-[#0c0c0d] border border-white/10 rounded-lg p-1.5 flex items-center">
                    <span className="text-[10px] text-zinc-500 font-mono w-4">W</span>
                    <input
                      type="number"
                      value={Math.round(selectedObj.width ? selectedObj.width * (selectedObj.scaleX || 1) : 0)}
                      onChange={(e) => updateSelectedProperty('width', e.target.value)}
                      className="bg-transparent border-0 w-full text-xs text-zinc-200 focus:outline-none p-0 ml-1 font-mono"
                    />
                  </div>
                  <div className="bg-[#0c0c0d] border border-white/10 rounded-lg p-1.5 flex items-center">
                    <span className="text-[10px] text-zinc-500 font-mono w-4">H</span>
                    <input
                      type="number"
                      value={Math.round(selectedObj.height ? selectedObj.height * (selectedObj.scaleY || 1) : 0)}
                      onChange={(e) => updateSelectedProperty('height', e.target.value)}
                      className="bg-transparent border-0 w-full text-xs text-zinc-200 focus:outline-none p-0 ml-1 font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* Opacity Option */}
              <div>
                <label className="text-[9px] font-bold text-zinc-400 block mb-1.5 uppercase tracking-wider">Opacity / Transparency</label>
                <div className="flex items-center space-x-3 bg-[#0c0c0d] border border-white/10 rounded-lg p-2">
                  <input
                    type="range"
                    min="10"
                    max="100"
                    value={Math.round((selectedObj.opacity ?? 1) * 100)}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value) / 100;
                      selectedObj.set('opacity', val);
                      canvas?.renderAll();
                      saveCanvasToState(canvas!, activeSlideIdxRef.current);
                      setSelectedObj({ ...selectedObj, opacity: val } as any);
                    }}
                    className="w-full h-1 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                  <span className="text-xs font-mono text-zinc-300 w-10 text-right">{Math.round((selectedObj.opacity ?? 1) * 100)}%</span>
                </div>
              </div>

              {/* Font Options for Text Elements */}
              {isTextObj && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[9px] font-bold text-zinc-400 block mb-1 uppercase tracking-wider">Size</label>
                      <input
                        type="number"
                        value={(selectedObj as any).fontSize || 24}
                        onChange={(e) => updateSelectedProperty('fontSize', e.target.value)}
                        className="w-full bg-[#0c0c0d] border border-white/10 rounded-lg px-2 py-1.5 text-xs text-zinc-200 focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-[9px] font-bold text-zinc-400 block mb-1 uppercase tracking-wider">Color</label>
                      <input
                        type="color"
                        value={selectedObj.fill as string || '#333333'}
                        onChange={(e) => updateSelectedProperty('fill', e.target.value)}
                        className="w-full h-[29px] bg-[#0c0c0d] border border-white/10 rounded-lg cursor-pointer p-0.5 focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[9px] font-bold text-zinc-400 block mb-1 uppercase tracking-wider">Content Text</label>
                    <textarea
                      value={(selectedObj as any).text || ''}
                      onChange={(e) => updateSelectedProperty('text', e.target.value)}
                      className="w-full bg-[#0c0c0d] border border-white/10 rounded-lg px-2.5 py-2 text-xs text-zinc-200 focus:outline-none leading-relaxed"
                      rows={5}
                    />
                  </div>
                </div>
              )}

              {/* Layers/Stacking controls inside Properties Panel */}
              <div className="space-y-2">
                <label className="text-[9px] font-bold text-zinc-400 block uppercase tracking-wider">Layer Actions</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => {
                      if (!canvas || !selectedObj) return;
                      canvas.bringToFront(selectedObj);
                      canvas.renderAll();
                      saveCanvasToState(canvas, activeSlideIdxRef.current);
                    }}
                    className="py-1.5 px-3 bg-white/[0.04] hover:bg-white/[0.08] text-xs font-semibold text-zinc-200 border border-white/10 rounded-lg transition-colors flex items-center justify-center"
                    title="Bring element to top layer"
                  >
                    Bring to Front
                  </button>
                  <button
                    onClick={() => {
                      if (!canvas || !selectedObj) return;
                      canvas.sendToBack(selectedObj);
                      // Make sure canvas background is still behind
                      const bg = canvas.backgroundImage;
                      if (bg && typeof bg !== 'string') {
                        canvas.sendToBack(bg as any);
                      }
                      canvas.renderAll();
                      saveCanvasToState(canvas, activeSlideIdxRef.current);
                    }}
                    className="py-1.5 px-3 bg-white/[0.04] hover:bg-white/[0.08] text-xs font-semibold text-zinc-200 border border-white/10 rounded-lg transition-colors flex items-center justify-center"
                    title="Send element to back layer"
                  >
                    Send to Back
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <button
                    onClick={() => {
                      if (!canvas || !selectedObj) return;
                      const activeObj = selectedObj as any;
                      const newLockState = !activeObj.lockMovementX;
                      activeObj.set({
                        lockMovementX: newLockState,
                        lockMovementY: newLockState,
                        lockScalingX: newLockState,
                        lockScalingY: newLockState,
                        lockRotation: newLockState,
                        hasControls: !newLockState
                      });
                      canvas.discardActiveObject();
                      canvas.renderAll();
                      saveCanvasToState(canvas, activeSlideIdxRef.current);
                      setSelectedObj(null);
                    }}
                    className={`py-1.5 px-3 text-xs font-semibold border rounded-lg transition-colors flex items-center justify-center ${selectedObj.lockMovementX
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                        : 'bg-white/[0.04] hover:bg-white/[0.08] text-zinc-200 border-white/10'
                      }`}
                  >
                    {selectedObj.lockMovementX ? 'Unlock Layer' : 'Lock Layer'}
                  </button>
                  <button
                    onClick={handleDeleteElement}
                    className="py-1.5 px-3 bg-red-500/10 hover:bg-red-500/20 text-xs font-semibold text-red-400 border border-red-500/20 rounded-lg transition-colors flex items-center justify-center"
                  >
                    Delete Element
                  </button>
                </div>
              </div>

              {/* Component Type Display */}
              {!isTextObj && (
                <div className="pt-1.5">
                  <div className="px-3 py-2 bg-indigo-500/10 rounded-lg text-[11px] font-semibold capitalize text-indigo-300 border border-indigo-500/20 shadow-inner">
                    {(selectedObj as any).elementType || selectedObj.type} Element
                  </div>
                </div>
              )}

            </div>
          </div>
        )}



      </div>

    </div>
  );
};

export default withStreamlitConnection(PptEditor);
