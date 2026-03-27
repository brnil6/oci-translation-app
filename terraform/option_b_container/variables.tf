variable "region" {
  type    = string
  default = "eu-frankfurt-1"
}

variable "compartment_id" {
  type        = string
  description = "OCI compartment OCID"
}

variable "subnet_id" {
  type        = string
  description = "OCID of the subnet for the container instance and load balancer"
}

variable "container_image" {
  type        = string
  description = "Full OCIR image path, e.g. fra.ocir.io/<namespace>/translate-api:latest"
}

variable "oci_compartment_id_env" {
  type        = string
  description = "OCI_COMPARTMENT_ID passed to the container for GenAI calls"
}

variable "oci_genai_endpoint" {
  type    = string
  default = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
}

variable "oci_default_model" {
  type    = string
  default = "cohere.command-a-03-2025"
}

variable "container_shape" {
  type    = string
  default = "CI.Standard.E4.Flex"
}

variable "container_ocpus" {
  type    = number
  default = 1
}

variable "container_memory_gb" {
  type    = number
  default = 2
}

variable "container_count" {
  type        = number
  default     = 1
  description = "Number of container instances (for availability)"
}
