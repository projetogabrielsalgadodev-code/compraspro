/** @type {import('next').NextConfig} */
const nextConfig = {
  // Aumentar o limite de body size para API routes que recebem upload de arquivos
  // O default é 1MB, aumentamos para 10MB para comportar planilhas grandes
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
};

export default nextConfig;
