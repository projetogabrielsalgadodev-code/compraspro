import { NextResponse } from "next/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const empresaId = searchParams.get("empresa_id");

  if (!empresaId) {
    return NextResponse.json({ error: "empresa_id obrigatorio" }, { status: 400 });
  }

  const response = await fetch(`${FASTAPI_URL}/api/configuracoes/empresa?empresa_id=${encodeURIComponent(empresaId)}`, {
    cache: "no-store"
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}

export async function PUT(request: Request) {
  const payload = await request.json();

  const response = await fetch(`${FASTAPI_URL}/api/configuracoes/empresa`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
