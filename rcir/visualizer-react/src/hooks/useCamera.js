import { useState, useCallback, useRef } from 'react';

export function useCamera(initialScale = 1, initialX = 0, initialY = 0) {
  const [camera, setCamera] = useState({ x: initialX, y: initialY, scale: initialScale });
  const isDragging = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    setCamera(prev => {
      const newScale = Math.max(0.1, Math.min(5.0, prev.scale * zoomFactor));
      return { ...prev, scale: newScale };
    });
  }, []);

  const handleMouseDown = useCallback((e) => {
    if (e.button === 0) { // Left click drag
      isDragging.current = true;
      dragStart.current = { x: e.clientX - camera.x, y: e.clientY - camera.y };
    }
  }, [camera.x, camera.y]);

  const handleMouseMove = useCallback((e) => {
    if (isDragging.current) {
      setCamera(prev => ({
        ...prev,
        x: e.clientX - dragStart.current.x,
        y: e.clientY - dragStart.current.y
      }));
    }
  }, []);

  const handleMouseUp = useCallback(() => {
    isDragging.current = false;
  }, []);

  const zoomIn = useCallback(() => {
    setCamera(prev => ({ ...prev, scale: Math.min(5.0, prev.scale * 1.25) }));
  }, []);

  const zoomOut = useCallback(() => {
    setCamera(prev => ({ ...prev, scale: Math.max(0.15, prev.scale * 0.8) }));
  }, []);

  const resetCamera = useCallback(() => {
    setCamera({ x: 0, y: 0, scale: 1 });
  }, []);

  return {
    camera,
    setCamera,
    handleWheel,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    zoomIn,
    zoomOut,
    resetCamera
  };
}
