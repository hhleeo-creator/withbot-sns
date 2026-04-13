// vite.config.js
import { defineConfig } from "file:///sessions/practical-ecstatic-lovelace/mnt/%EC%9C%84%EB%93%9C%EB%B4%87%20%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8/withbot/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///sessions/practical-ecstatic-lovelace/mnt/%EC%9C%84%EB%93%9C%EB%B4%87%20%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8/withbot/frontend/node_modules/@vitejs/plugin-react/dist/index.js";
var vite_config_default = defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/auth": "http://localhost:8000",
      "/ai-guide": "http://localhost:8000",
      "/uploads": "http://localhost:8000"
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcuanMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvc2Vzc2lvbnMvcHJhY3RpY2FsLWVjc3RhdGljLWxvdmVsYWNlL21udC9cdUM3MDRcdUI0RENcdUJEMDcgXHVENTA0XHVCODVDXHVDODFEXHVEMkI4L3dpdGhib3QvZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIi9zZXNzaW9ucy9wcmFjdGljYWwtZWNzdGF0aWMtbG92ZWxhY2UvbW50L1x1QzcwNFx1QjREQ1x1QkQwNyBcdUQ1MDRcdUI4NUNcdUM4MURcdUQyQjgvd2l0aGJvdC9mcm9udGVuZC92aXRlLmNvbmZpZy5qc1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vc2Vzc2lvbnMvcHJhY3RpY2FsLWVjc3RhdGljLWxvdmVsYWNlL21udC8lRUMlOUMlODQlRUIlOTMlOUMlRUIlQjQlODclMjAlRUQlOTQlODQlRUIlQTElOUMlRUMlQTAlOUQlRUQlOEElQjgvd2l0aGJvdC9mcm9udGVuZC92aXRlLmNvbmZpZy5qc1wiO2ltcG9ydCB7IGRlZmluZUNvbmZpZyB9IGZyb20gJ3ZpdGUnXG5pbXBvcnQgcmVhY3QgZnJvbSAnQHZpdGVqcy9wbHVnaW4tcmVhY3QnXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFtyZWFjdCgpXSxcbiAgc2VydmVyOiB7XG4gICAgcG9ydDogNTE3MyxcbiAgICBwcm94eToge1xuICAgICAgJy9hcGknOiAnaHR0cDovL2xvY2FsaG9zdDo4MDAwJyxcbiAgICAgICcvYXV0aCc6ICdodHRwOi8vbG9jYWxob3N0OjgwMDAnLFxuICAgICAgJy9haS1ndWlkZSc6ICdodHRwOi8vbG9jYWxob3N0OjgwMDAnLFxuICAgICAgJy91cGxvYWRzJzogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODAwMCcsXG4gICAgfVxuICB9XG59KVxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUFxYixTQUFTLG9CQUFvQjtBQUNsZCxPQUFPLFdBQVc7QUFFbEIsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDMUIsU0FBUyxDQUFDLE1BQU0sQ0FBQztBQUFBLEVBQ2pCLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNMLFFBQVE7QUFBQSxNQUNSLFNBQVM7QUFBQSxNQUNULGFBQWE7QUFBQSxNQUNiLFlBQVk7QUFBQSxJQUNkO0FBQUEsRUFDRjtBQUNGLENBQUM7IiwKICAibmFtZXMiOiBbXQp9Cg==
