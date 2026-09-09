package com.example.iotchallenge

import android.util.Log
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.util.concurrent.atomic.AtomicInteger

object TinyIoTApi {

    // ✅ RouteSelection con(JSON) 파싱 결과
    data class RouteInfo(
        val timestamp: String? = null,
        val routeId: Int? = null,
        val routeName: String? = null,
        val userLocation: String? = null,
        val estimatedTime: Int? = null,
        val safetyLevel: String? = null,
        val reason: String? = null
    )

    // ✅ 앱에서 한 번에 쓰기 좋은 LiveState
    data class LiveState(
        val routeInfo: RouteInfo?,
        val room1Fire: String?,
        val room2Fire: String?,
        val earthquake: String?,      // ✅ Sensors/EarthquakeStatus
        val stairsPassable: String?,
        val crowd: Int?,              // ✅ Result/CrowdCount
        val temperature: Double?,
        val humidity: Double?,
        val co2: Int?,
        val clientPosition: Int?
    )

    // ========== 서버 설정 ==========
    private const val BASE_URL = "https://onem2m.iotcoss.ac.kr"
    private const val ORIGIN = "CAdmin"
    private const val RVI = "2a"

    // ⚠️ 실제 배포/공유할 거면 BuildConfig 또는 local.properties로 빼는 걸 추천
    private const val API_KEY = "YOUR_API_KEY"      // 발급받은 tinyIoT API 키로 교체
    private const val LECTURE = "YOUR_LECTURE_ID"   // 예: LCT_XXXXXXXX
    private const val CREATOR = "YOUR_CREATOR_ID"   // 예: sjuXXXXXXXX

    private val client = OkHttpClient()

    // oneM2M 최신 CIN(/la)에서 "con"만 꺼내기
    fun fetchLatestCon(path: String, onResult: (String?) -> Unit) {
        val url = "$BASE_URL$path"
        Log.d("TINYIOT_HTTP", "REQ url=$url")

        val req = Request.Builder()
            .url(url)
            .addHeader("Accept", "application/json")
            // ✅ RI는 없어도 되는데, oneM2M 관례상 있으면 좋음 (요청 식별자)
            .addHeader("X-M2M-RI", "android-${System.currentTimeMillis()}")
            .addHeader("X-M2M-Origin", ORIGIN)
            .addHeader("X-M2M-RVI", RVI)
            .addHeader("X-API-KEY", API_KEY)
            .addHeader("X-AUTH-CUSTOM-LECTURE", LECTURE)
            .addHeader("X-AUTH-CUSTOM-CREATOR", CREATOR)
            .build()

        client.newCall(req).enqueue(object : okhttp3.Callback {
            override fun onFailure(call: okhttp3.Call, e: java.io.IOException) {
                Log.e("TINYIOT_HTTP", "FAIL url=$url err=${e.message}", e)
                onResult(null)
            }

            override fun onResponse(call: okhttp3.Call, response: okhttp3.Response) {
                response.use {
                    if (!it.isSuccessful) {
                        Log.e("TINYIOT_HTTP", "HTTP ${it.code} url=$url")
                        onResult(null)
                        return
                    }
                    val body = it.body?.string() ?: run {
                        onResult(null); return
                    }

                    val con = try {
                        val json = JSONObject(body)
                        val cin = when {
                            json.has("m2m:cin") -> json.getJSONObject("m2m:cin")
                            json.has("cin") -> json.getJSONObject("cin")
                            else -> null
                        }
                        cin?.optString("con", null)
                    } catch (e: Exception) {
                        null
                    }

                    onResult(con)
                }
            }
        })
    }

    // =========================
    // ✅ Paths (리소스 트리 반영)
    // =========================

    // Sensors
    private const val P_TEMP = "/tinyIoT/SmartEvacGuide/Sensors/Temperature/la"
    private const val P_HUMI = "/tinyIoT/SmartEvacGuide/Sensors/Humidity/la"
    private const val P_CO2  = "/tinyIoT/SmartEvacGuide/Sensors/CO2/la"
    private const val P_POS  = "/tinyIoT/SmartEvacGuide/Sensors/ClientPosition/la"
    private const val P_EQ   = "/tinyIoT/SmartEvacGuide/Sensors/EarthquakeStatus/la" // ✅ moved here

    // Result
    private fun pResult(name: String) =
        "/tinyIoT/SmartEvacGuide/Result/$name/la"

    private const val P_CROWD = "/tinyIoT/SmartEvacGuide/Detection/CrowdCount/la"

    // =========================
    // ✅ Sensors fetch
    // =========================

    fun fetchTemperature(onResult: (Double?) -> Unit) {
        fetchLatestCon(P_TEMP) { con -> onResult(con?.trim()?.toDoubleOrNull()) }
    }

    fun fetchHumidity(onResult: (Double?) -> Unit) {
        fetchLatestCon(P_HUMI) { con -> onResult(con?.trim()?.toDoubleOrNull()) }
    }

    fun fetchCO2(onResult: (Int?) -> Unit) {
        fetchLatestCon(P_CO2) { con -> onResult(con?.trim()?.toIntOrNull()) }
    }

    fun fetchClientPosition(onResult: (Int?) -> Unit) {
        fetchLatestCon(P_POS) { con ->
            onResult(con?.trim()?.toIntOrNull())
        }
    }

    fun fetchEarthquake(onResult: (String?) -> Unit) {
        fetchLatestCon(P_EQ) { con -> onResult(con?.trim()) }
    }

    // =========================
    // ✅ Result fetch
    // =========================

    fun fetchResultStatus(name: String, onResult: (String?) -> Unit) {
        fetchLatestCon(pResult(name), onResult)
    }

    // ✅ RouteSelection: con이 JSON이면 RouteInfo로 파싱
    fun fetchRouteInfo(onResult: (RouteInfo?) -> Unit) {
        fetchLatestCon(pResult("RouteSelection")) { con ->
            if (con == null) { onResult(null); return@fetchLatestCon }

            val info = try {
                val obj = JSONObject(con)
                RouteInfo(
                    timestamp = obj.optString("timestamp", null),
                    routeId = if (obj.has("route_id")) obj.optInt("route_id") else null,
                    routeName = obj.optString("route_name", null),
                    userLocation = obj.optString("user_location", null),
                    estimatedTime = if (obj.has("estimated_time")) obj.optInt("estimated_time") else null,
                    safetyLevel = obj.optString("safety_level", null),
                    reason = obj.optString("reason", null)
                )
            } catch (e: Exception) {
                RouteInfo(routeId = con.trim().toIntOrNull())
            }

            onResult(info)
        }
    }

    // ✅ 한 번에 모두 모아서 콜백
    fun fetchLiveState(onResult: (LiveState) -> Unit) {
        var routeInfo: RouteInfo? = null
        var r1: String? = null
        var r2: String? = null
        var eq: String? = null
        var stairs: String? = null
        var crowd: Int? = null
        var temp: Double? = null
        var humi: Double? = null
        var co2: Int? = null
        var pos: Int? = null

        val done = AtomicInteger(0)
        fun finishOne() {
            if (done.incrementAndGet() == 10) {
                onResult(
                    LiveState(
                        routeInfo = routeInfo,
                        room1Fire = r1,
                        room2Fire = r2,
                        earthquake = eq,
                        stairsPassable = stairs,
                        crowd = crowd,
                        temperature = temp,
                        humidity = humi,
                        co2 = co2,
                        clientPosition = pos
                    )
                )
            }
        }

        fetchRouteInfo { v -> routeInfo = v; finishOne() }

        // ✅ Result/ 아래
        fetchResultStatus("Room1FireStatus") { v -> r1 = v; finishOne() }
        fetchResultStatus("Room2FireStatus") { v -> r2 = v; finishOne() }
        fetchResultStatus("StairsPassable") { v -> stairs = v; finishOne() }

        fetchLatestCon(P_CROWD) { v ->
            crowd = v?.trim()?.toIntOrNull()
            finishOne()
        }

        // ✅ Sensors/ 아래
        fetchEarthquake { v -> eq = v; finishOne() } // ✅ moved here
        fetchTemperature { v -> temp = v; finishOne() }
        fetchHumidity { v -> humi = v; finishOne() }
        fetchCO2 { v -> co2 = v; finishOne() }
        fetchClientPosition { v -> pos = v; finishOne() }
    }
}