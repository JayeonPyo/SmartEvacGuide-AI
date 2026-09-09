package com.example.iotchallenge

import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import android.view.View
import kotlin.math.min

class RouteOverlayView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null
) : View(context, attrs) {

    // 정규화(0~1) 경로
    private var route: List<Pair<Float, Float>> = emptyList()

    // 사용자 마커(0~1)
    private var userMarker: Pair<Float, Float>? = null

    // 화재 마커(방1/방2) (0~1)
    private var fireMarker1: Pair<Float, Float>? = null
    private var fireMarker2: Pair<Float, Float>? = null

    // 혼잡도 마커(계단) (0~1 + count)
    private var crowdMarker: Pair<Float, Float>? = null
    private var crowdCount: Int? = null

    private var earthquakeOn: Boolean = false

    private val paintRoute = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.RED
        style = Paint.Style.STROKE
        strokeWidth = 18f
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }

    private val paintDot = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }

    private val paintText = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.BLACK
        textSize = 42f
        typeface = Typeface.DEFAULT_BOLD
    }

    private val warningCirclePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.rgb(255, 193, 7) // amber 느낌
        style = Paint.Style.FILL
    }

    private val warningTextPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.BLACK
        textSize = 28f
        textAlign = Paint.Align.CENTER
        typeface = Typeface.DEFAULT_BOLD
    }

    fun setRouteNormalized(points: List<Pair<Float, Float>>) {
        route = points
        invalidate()
    }

    fun setUserMarkerNormalized(p: Pair<Float, Float>?) {
        userMarker = p
        invalidate()
    }

    fun setFireMarkers(room1: Pair<Float, Float>?, room2: Pair<Float, Float>?) {
        fireMarker1 = room1
        fireMarker2 = room2
        invalidate()
    }

    fun setCrowdMarker(p: Pair<Float, Float>?, count: Int?) {
        crowdMarker = p
        crowdCount = count
        invalidate()
    }

    fun setEarthquakeMarker(on: Boolean) {
        earthquakeOn = on
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        // 좌표 변환 함수 (정규화 -> 픽셀)
        fun toPx(p: Pair<Float, Float>): Pair<Float, Float> {
            val x = p.first * width
            val y = p.second * height
            return x to y
        }

        // 1) 경로 그리기
        if (route.size >= 2) {
            val path = Path()
            val (sx, sy) = toPx(route.first())
            path.moveTo(sx, sy)
            for (i in 1 until route.size) {
                val (x, y) = toPx(route[i])
                path.lineTo(x, y)
            }
            canvas.drawPath(path, paintRoute)
        }

        // 2) 사용자 위치 (파란 점)
        userMarker?.let {
            val (x, y) = toPx(it)
            paintDot.color = Color.parseColor("#1976D2")
            canvas.drawCircle(x, y, 28f, paintDot)
            paintText.color = Color.parseColor("#1976D2")
            canvas.drawText("YOU", x + 30f, y - 20f, paintText)
        }

        // 3) 화재 위치 (🔥)
        fun drawFire(p: Pair<Float, Float>) {
            val (x, y) = toPx(p)
            paintDot.color = Color.parseColor("#D32F2F")
            canvas.drawCircle(x, y, 26f, paintDot)
            paintText.color = Color.parseColor("#D32F2F")
            canvas.drawText("🔥", x + 22f, y + 16f, paintText)
        }

        if (earthquakeOn) {
            val x = width * 0.86f
            val y = height * 0.12f

            paintText.color = Color.parseColor("#F9A825") // 노란 경고색 (원하면 변경)
            paintText.textSize = 55f
            paintText.textAlign = Paint.Align.CENTER

            canvas.drawText("⚠️", x, y + 18f, paintText)

            // 원상복구
            paintText.textAlign = Paint.Align.LEFT
        }

        fireMarker1?.let { drawFire(it) }
        fireMarker2?.let { drawFire(it) }

        // 4) 혼잡도 (👤 + 숫자)
        crowdMarker?.let {
            val (x, y) = toPx(it)
            paintDot.color = Color.parseColor("#F9A825")
            canvas.drawCircle(x, y, 26f, paintDot)
            paintText.color = Color.parseColor("#F9A825")
            val c = crowdCount ?: 0
            canvas.drawText("👤$c", x + 22f, y + 16f, paintText)
        }
    }
}