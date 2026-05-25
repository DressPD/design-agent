resource "aws_cloudfront_origin_access_control" "site" {
  name                              = "${var.project_prefix}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_function" "spa_router" {
  name    = "${var.project_prefix}-spa-router"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-EOF
    function handler(event) {
      var request = event.request;
      var uri = request.uri;
      if (uri === '/' || uri === '') return request;
      if (/\/[^/]+\.[^/]+$/.test(uri)) return request;
      var parts = uri.split('/').filter(function(p) { return p !== ''; });
      if (parts.length > 0) {
        request.uri = '/' + parts[0] + '/index.html';
      }
      return request;
    }
  EOF
}

resource "aws_cloudfront_distribution" "site" {
  enabled      = true
  price_class  = "PriceClass_100"
  http_version = "http2and3"

  origin {
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_id                = "s3-site"
    origin_access_control_id = aws_cloudfront_origin_access_control.site.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-site"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_router.arn
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Project   = var.project_prefix
    ManagedBy = "terraform"
  }
}
