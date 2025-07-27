import { NextResponse } from "next/server"
import axios from "axios"

export async function GET() {
    try {
        // Call your actual community videos API
        const response = await axios.get("http://127.0.0.1:8000/videos/completed", {
            headers: {
                accept: "application/json",
            },
        })

        return NextResponse.json(response.data)
    } catch (error) {
        console.error("Error fetching community videos:", error)

        if (axios.isAxiosError(error)) {
            const status = error.response?.status || 500
            const message = error.response?.data?.detail || "Failed to fetch community videos"
            return NextResponse.json({ error: message }, { status })
        }

        return NextResponse.json({ error: "Failed to fetch community videos" }, { status: 500 })
    }
}
