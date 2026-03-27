# --- Container Instance ---
# Auth: the container uses API key authentication via OCI config
# mounted as a volume from Vault or baked into the image.
# The code in core/auth.py falls back to ~/.oci/config automatically.

resource "oci_container_instances_container_instance" "translate" {
  count = var.container_count

  compartment_id               = var.compartment_id
  availability_domain          = data.oci_identity_availability_domains.ads.availability_domains[count.index % length(data.oci_identity_availability_domains.ads.availability_domains)].name
  display_name                 = "translate-api-${count.index}"
  container_restart_policy     = "ALWAYS"
  graceful_shutdown_timeout_in_seconds = 30

  shape = var.container_shape
  shape_config {
    ocpus         = var.container_ocpus
    memory_in_gbs = var.container_memory_gb
  }

  vnics {
    subnet_id  = var.subnet_id
    is_public_ip_assigned = true
  }

  containers {
    display_name = "translate-api"
    image_url    = var.container_image

    environment_variables = {
      OCI_COMPARTMENT_ID = var.oci_compartment_id_env
      OCI_GENAI_ENDPOINT = var.oci_genai_endpoint
      OCI_DEFAULT_MODEL  = var.oci_default_model
      OCI_AUTH           = "api_key"
    }

    resource_config {
      vcpus_limit         = var.container_ocpus
      memory_limit_in_gbs = var.container_memory_gb
    }

    health_checks {
      health_check_type = "HTTP"
      port              = 8000
      path              = "/docs"
      interval_in_seconds          = 10
      timeout_in_seconds           = 5
      success_threshold            = 1
      failure_threshold            = 3
      failure_action               = "KILL"
    }
  }
}

# --- Load Balancer ---

resource "oci_load_balancer_load_balancer" "translate" {
  compartment_id = var.compartment_id
  display_name   = "translate-api-lb"
  shape          = "flexible"
  subnet_ids     = [var.subnet_id]
  is_private     = false

  shape_details {
    minimum_bandwidth_in_mbps = 10
    maximum_bandwidth_in_mbps = 100
  }
}

resource "oci_load_balancer_backend_set" "translate" {
  load_balancer_id = oci_load_balancer_load_balancer.translate.id
  name             = "translate-api-backends"
  policy           = "ROUND_ROBIN"

  health_checker {
    protocol          = "HTTP"
    port              = 8000
    url_path          = "/docs"
    interval_ms       = 10000
    timeout_in_millis = 5000
    retries           = 3
  }
}

resource "oci_load_balancer_backend" "translate" {
  count = var.container_count

  load_balancer_id = oci_load_balancer_load_balancer.translate.id
  backendset_name  = oci_load_balancer_backend_set.translate.name
  ip_address       = oci_container_instances_container_instance.translate[count.index].vnics[0].private_ip
  port             = 8000
}

resource "oci_load_balancer_listener" "translate" {
  load_balancer_id         = oci_load_balancer_load_balancer.translate.id
  name                     = "translate-api-listener"
  default_backend_set_name = oci_load_balancer_backend_set.translate.name
  port                     = 443
  protocol                 = "HTTP"
}

# --- Data sources ---

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

# --- Outputs ---

output "load_balancer_ip" {
  value = oci_load_balancer_load_balancer.translate.ip_address_details[0].ip_address
}

output "translate_endpoint" {
  value = "http://${oci_load_balancer_load_balancer.translate.ip_address_details[0].ip_address}/translate"
}
