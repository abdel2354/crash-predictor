import { NextRequest, NextResponse } from "next/server";

const ACCESS_KEY = process.env.ACCESS_KEY || "HATIM200707";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { password } = body as { password: string };

  if (!password) {
    return NextResponse.json({ success: false }, { status: 400 });
  }

  if (password === ACCESS_KEY) {
    return NextResponse.json({ success: true });
  }

  return NextResponse.json({ success: false }, { status: 401 });
}
