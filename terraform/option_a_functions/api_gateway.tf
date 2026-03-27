resource "oci_apigateway_gateway" "translate_gw" {
  compartment_id = var.compartment_id
  endpoint_type  = "PUBLIC"
  subnet_id      = var.subnet_id
  display_name   = "translate-with-llm-gateway"
}

resource "oci_apigateway_deployment" "translate_deploy" {
  compartment_id = var.compartment_id
  gateway_id     = oci_apigateway_gateway.translate_gw.id
  path_prefix    = "/v1"
  display_name   = "translate-with-llm-deployment"

  specification {
    routes {
      path    = "/translate"
      methods = ["POST"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = var.function_id
      }
    }
  }
}

output "api_gateway_endpoint" {
  value = "${oci_apigateway_gateway.translate_gw.hostname}/v1/translate"
}
