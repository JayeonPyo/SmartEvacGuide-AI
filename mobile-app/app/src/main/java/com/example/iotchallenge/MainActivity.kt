package com.example.iotchallenge

import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.dialog.MaterialAlertDialogBuilder

class MainActivity : AppCompatActivity() {

    // ===== 2F 정규화 좌표(0~1) =====
    private val R1 = 0.20578505f to 0.24762176f
    private val R2 = 0.7168145f to 0.68293476f
    private val CS = 0.176698f to 0.8105537f
    private val S2 = 0.9306837f to 0.8740644f
    private val J  = 0.2429464f to 0.80649894f
    private val K  = 0.35740912f to 0.8006515f

    private val routes2F: Map<Int, List<Pair<Float, Float>>> by lazy {
        mapOf(
            1 to listOf(R1, K, J, CS),
            2 to listOf(R1, K, S2),
            3 to listOf(R2, K, J, CS),
            4 to listOf(R2, S2),
            5 to listOf(J, CS),
            6 to listOf(J, K, S2)
        )
    }

    private enum class UserLocation { ROOM1, ROOM2, STAIRS }
    private var userLocation: UserLocation = UserLocation.ROOM1

    private lateinit var mapView: ImageView
    private lateinit var overlay: RouteOverlayView
    private lateinit var tvStatus: TextView
    private lateinit var tvSensors: TextView
    private lateinit var tvStatusDetail: TextView
    private lateinit var btnLocation: Button

    private var lastRoom1Fire: String? = null
    private var lastRoom2Fire: String? = null
    private var alertShowing = false

    private var lastEarthquake: String? = null
    private var eqAlertShowing = false

    private val handler = Handler(Looper.getMainLooper())
    private var polling = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        mapView = findViewById(R.id.imageViewMap)
        overlay = findViewById(R.id.routeOverlayView)
        tvStatus = findViewById(R.id.tvStatus)
        tvSensors = findViewById(R.id.tvSensors)
        tvStatusDetail = findViewById(R.id.tvStatusDetail)
        btnLocation = findViewById(R.id.btnLocation)

        mapView.setImageResource(R.drawable.map_2f)

        // 초기 마커
        applyUserMarker()

        btnLocation.setOnClickListener { showLocationDialog() }

        startPolling()
    }

    private fun showLocationDialog() {
        val items = arrayOf("방1", "방2", "계단")
        val checked = when (userLocation) {
            UserLocation.ROOM1 -> 0
            UserLocation.ROOM2 -> 1
            UserLocation.STAIRS -> 2
        }

        AlertDialog.Builder(this)
            .setTitle("📍 현재 어디에 계신가요?")
            .setSingleChoiceItems(items, checked) { _, which ->
                userLocation = when (which) {
                    0 -> UserLocation.ROOM1
                    1 -> UserLocation.ROOM2
                    else -> UserLocation.STAIRS
                }
            }
            .setPositiveButton("확인") { dialog, _ ->
                applyUserMarker()
                dialog.dismiss()
            }
            .setNegativeButton("취소") { dialog, _ -> dialog.dismiss() }
            .show()
    }

    private fun applyUserMarker() {
        val p = when (userLocation) {
            UserLocation.ROOM1 -> R1
            UserLocation.ROOM2 -> R2
            UserLocation.STAIRS -> CS
        }
        overlay.setUserMarkerNormalized(p)
    }

    private fun startPolling() {
        if (polling) return
        polling = true

        val task = object : Runnable {
            override fun run() {
                TinyIoTApi.fetchLiveState { state ->
                    runOnUiThread {
                        val offline = (state.routeInfo == null
                                && state.room1Fire == null
                                && state.room2Fire == null
                                && state.earthquake == null
                                && state.stairsPassable == null
                                && state.crowd == null
                                && state.temperature == null
                                && state.humidity == null
                                && state.co2 == null)

                        if (offline) {
                            tvStatus.text = "OFFLINE (서버 응답 없음)"
                            tvStatus.setTextColor(Color.GRAY)
                            tvSensors.text = "Temp: -  Humi: -  CO2: -"
                            tvStatusDetail.text = "R1Fire: -  R2Fire: -  EQ: -  Stairs: -  Crowd: -"

                            overlay.setRouteNormalized(emptyList())
                            overlay.setFireMarkers(null, null)
                            overlay.setCrowdMarker(null, null)
                        } else {
                            val rid = state.routeInfo?.routeId
                            val serverPos = state.clientPosition
                            if (serverPos != null) {
                                userLocation = when (serverPos) {
                                    1 -> UserLocation.ROOM1
                                    2 -> UserLocation.ROOM2
                                    3 -> UserLocation.STAIRS
                                    else -> userLocation
                                }
                                applyUserMarker()
                            }

                            val locLabel = when (userLocation) {
                                UserLocation.ROOM1 -> "방1"
                                UserLocation.ROOM2 -> "방2"
                                UserLocation.STAIRS -> "계단"
                            }
                            tvStatus.text = "실시간 안내 (Route: ${rid ?: "-"}) · 위치: $locLabel"
                            tvStatus.setTextColor(Color.RED)

                            val t = state.temperature?.let { String.format("%.1f", it) } ?: "-"
                            val h = state.humidity?.let { String.format("%.1f", it) } ?: "-"
                            val c = state.co2?.toString() ?: "-"

                            tvSensors.text = "Temp: $t  Humi: $h  CO2: $c"

                            val crowd = state.crowd?.toString() ?: "-"

                            tvStatusDetail.text =
                                "R1Fire: ${state.room1Fire ?: "-"}  " +
                                        "R2Fire: ${state.room2Fire ?: "-"}  " +
                                        "EQ: ${state.earthquake ?: "-"}  " +
                                        "Stairs: ${state.stairsPassable ?: "-"}  " +
                                        "Crowd: $crowd"

                            val points = if (rid != null) routes2F[rid] ?: emptyList() else emptyList()
                            overlay.setRouteNormalized(points)

                            val r1Fire = state.room1Fire?.trim()?.lowercase() == "yes"
                            val r2Fire = state.room2Fire?.trim()?.lowercase() == "yes"
                            overlay.setFireMarkers(
                                room1 = if (r1Fire) R1 else null,
                                room2 = if (r2Fire) R2 else null
                            )

                            overlay.setCrowdMarker(CS, state.crowd ?: 0)

                            val r1 = state.room1Fire?.lowercase()
                            val r2 = state.room2Fire?.lowercase()

                            val r1Triggered = (lastRoom1Fire != "yes" && r1 == "yes")
                            val r2Triggered = (lastRoom2Fire != "yes" && r2 == "yes")

                            lastRoom1Fire = r1
                            lastRoom2Fire = r2

                            if (!alertShowing && (r1Triggered || r2Triggered)) {
                                val msg = when {
                                    r1Triggered -> "방1에 화재가 발생하였습니다.\n신속히 대피 바랍니다."
                                    r2Triggered -> "방2에 화재가 발생하였습니다.\n신속히 대피 바랍니다."
                                    else -> "화재가 발생하였습니다.\n신속히 대피 바랍니다."
                                }
                                showFireAlert(msg)
                            }

                            val eqNow = state.earthquake?.trim()?.lowercase()
                            val eqTriggered = (lastEarthquake != "yes" && eqNow == "yes")
                            lastEarthquake = eqNow

                            // ✅ 지도에 지진 표시 (지진이 yes면 표시, 아니면 제거)
                            overlay.setEarthquakeMarker(if (eqNow == "yes") true else false)

                            // ✅ 새로 yes로 바뀌는 순간에만 Alert
                            if (!eqAlertShowing && eqTriggered) {
                                showEarthquakeAlert("지진이 감지되었습니다.\n낮은 자세로 몸을 보호하고, 흔들림이 멈춘 후 대피하세요.")
                            }
                        }
                    }
                }

                handler.postDelayed(this, 2000)
            }
        }

        handler.post(task)
    }

    private fun showFireAlert(message: String) {
        alertShowing = true
        MaterialAlertDialogBuilder(this, R.style.ThemeOverlay_IoTChallenge_RoundedDialog)
            .setTitle("🔥 화재 경보")
            .setMessage(message)
            .setCancelable(false)
            .setPositiveButton("확인") { d, _ ->
                alertShowing = false
                d.dismiss()
            }
            .show()
    }

    private fun showEarthquakeAlert(message: String) {
        eqAlertShowing = true
        MaterialAlertDialogBuilder(this, R.style.ThemeOverlay_IoTChallenge_RoundedDialog)
            .setTitle("⚠️ 지진 경보")
            .setMessage(message)
            .setCancelable(false)
            .setPositiveButton("확인") { d, _ ->
                eqAlertShowing = false
                d.dismiss()
            }
            .show()
    }

    override fun onDestroy() {
        super.onDestroy()
        polling = false
        handler.removeCallbacksAndMessages(null)
    }
}