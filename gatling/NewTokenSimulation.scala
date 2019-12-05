package wazosimulation

import scala.concurrent.duration._

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import io.gatling.jdbc.Predef._

class NewTokenSimulation extends Simulation {

	val httpProtocol = http
		.baseUrl("https://wazo.vagrant")
		.inferHtmlResources()
		.acceptHeader("*/*")
		.contentTypeHeader("application/json")
		.userAgentHeader("curl/7.47.0")

	val scn = scenario("NewTokenSimulation")
		.exec(http("request_0")
			.post("/api/auth/0.1/token")
			.body(RawFileBody("wazosimulation/newtokensimulation/0000_request.json"))
			.basicAuth("root","wazo"))

	setUp(scn.inject(atOnceUsers(10))).protocols(httpProtocol)
	// setUp(scn.inject(constantConcurrentUsers(10) during (60 seconds))).protocols(httpProtocol)
}
