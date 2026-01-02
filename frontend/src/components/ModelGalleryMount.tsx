import { useEffect, useRef } from 'react';
import { createApp } from 'vue';
import ModelGallery from '@/components/ModelGallery.vue';

const ModelGalleryMount = () => {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) return undefined;
    const app = createApp(ModelGallery);
    app.mount(containerRef.current);

    return () => {
      app.unmount();
    };
  }, []);

  return <div ref={containerRef} className="min-h-[300px]" />;
};

export default ModelGalleryMount;
