import { NextResponse } from "next/server";
import crypto from "crypto";

const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET;

/**
 * Webhook handler — valida HMAC antes de processar.
 * 
 * Se WEBHOOK_SECRET estiver configurado, verifica o header x-webhook-signature.
 * Se não estiver configurado, rejeita todas as requests por segurança.
 */
export async function POST(request: Request) {
  // SEGURANÇA: Rejeitar se WEBHOOK_SECRET não configurado
  if (!WEBHOOK_SECRET) {
    console.warn("[webhook] WEBHOOK_SECRET não configurado. Request rejeitado.");
    return NextResponse.json(
      { error: "Webhook não configurado." },
      { status: 503 }
    );
  }

  // Validar HMAC signature
  const signature = request.headers.get("x-webhook-signature");
  if (!signature) {
    return NextResponse.json(
      { error: "Assinatura ausente." },
      { status: 401 }
    );
  }

  const rawBody = await request.text();

  const expectedSignature = crypto
    .createHmac("sha256", WEBHOOK_SECRET)
    .update(rawBody)
    .digest("hex");

  const isValid = crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );

  if (!isValid) {
    return NextResponse.json(
      { error: "Assinatura inválida." },
      { status: 401 }
    );
  }

  // Processar payload seguro
  try {
    const body = JSON.parse(rawBody);
    console.log("[webhook] Payload recebido:", JSON.stringify(body).slice(0, 200));

    // TODO: Implementar lógica de processamento do webhook aqui
    
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "Payload inválido." }, { status: 400 });
  }
}
