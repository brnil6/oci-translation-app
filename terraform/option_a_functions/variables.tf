variable "region" {
  type    = string
  default = "eu-frankfurt-1"
}

variable "compartment_id" {
  type        = string
  description = "OCI compartment OCID"
}

variable "function_id" {
  type        = string
  description = "OCID of the deployed OCI Function"
}

variable "subnet_id" {
  type        = string
  description = "OCID of the subnet for the API Gateway"
}
