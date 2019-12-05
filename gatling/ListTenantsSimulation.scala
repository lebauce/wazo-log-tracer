package wazosimulation

import scala.concurrent.duration._

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import io.gatling.jdbc.Predef._

class ListTenantsSimulation extends Simulation {

	val httpProtocol = http
		.baseUrl("https://wazo.vagrant")
		.inferHtmlResources()
		.acceptHeader("*/*")
		.contentTypeHeader("application/json")
		.userAgentHeader("curl/7.47.0")

	val headers_0 = Map(
		"Wazo-Tenant" -> "c8858758-7824-4a1e-8a79-08b6dde2af9c",
		"X-Auth-Token" -> "3d88fb90-f429-4431-9077-a8cddfed9bc4")



	val scn = scenario("ListTenantsSimulation")
		.exec(http("request_0")
			.get("/api/auth/0.1/tenants")
			.headers(headers_0)
			.body(RawFileBody("wazosimulation/listtenantssimulation/0000_request.json")))

	// setUp(scn.inject(atOnceUsers(100))).protocols(httpProtocol)
	setUp(scn.inject(constantConcurrentUsers(10) during (60 seconds))).protocols(httpProtocol)
}
