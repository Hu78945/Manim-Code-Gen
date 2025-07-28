import { type NextRequest, NextResponse } from "next/server"
import axios from "axios"

export async function POST(request: NextRequest) {
    try {
        const { prompt, quality = "low" } = await request.json()

        if (!prompt) {
            return NextResponse.json({ error: "Prompt is required" }, { status: 400 })
        }

        // Call your actual video generation API
        const response = await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL}generate-video/`,
            {
                prompt,
                quality,
                max_retries: 5,
            },
            {
                headers: {
                    accept: "application/json",
                    "Content-Type": "application/json",
                },
            },
        )

        return NextResponse.json(response.data)
    } catch (error) {
        console.error("Error generating video:", error)

        if (axios.isAxiosError(error)) {
            const status = error.response?.status || 500
            const message = error.response?.data?.detail || "Failed to start video generation"
            return NextResponse.json({ error: message }, { status })
        }

        return NextResponse.json({ error: "Failed to start video generation" }, { status: 500 })
    }
}
