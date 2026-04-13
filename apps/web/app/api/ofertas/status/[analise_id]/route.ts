import { NextResponse } from "next/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

export async function GET(
  _request: Request,
  { params }: { params: { analise_id: string } }
) {
  try {
    const { analise_id } = params;

    const response = await fetch(
      `${FASTAPI_URL}/api/ofertas/status/${analise_id}`,
      { cache: "no-store" }
    );

    if (!response.ok) {
      const errorBody = await response.text();
      return NextResponse.json({ error: errorBody }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    console.error("[status] Erro:", err);
    return NextResponse.json({ error: "Erro ao consultar status." }, { status: 500 });
  }
}
