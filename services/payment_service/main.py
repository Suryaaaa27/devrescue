from fastapi import FastAPI, HTTPException
import logging
import random
import time

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.trace import Status, StatusCode
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
)
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)

logger = logging.getLogger("payment-service")


# =========================================================
# OpenTelemetry Resource
# =========================================================

resource = Resource.create(
    {
        "service.name": "payment-service",
        "service.version": "0.1.0",
        "deployment.environment": "development",
    }
)


# =========================================================
# OpenTelemetry Logging
# =========================================================

logger_provider = LoggerProvider(
    resource=resource
)

otlp_log_exporter = OTLPLogExporter(
    endpoint="http://127.0.0.1:4318/v1/logs",
)

logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(
        otlp_log_exporter
    )
)

set_logger_provider(
    logger_provider
)

otel_logging_handler = LoggingHandler(
    level=logging.INFO,
    logger_provider=logger_provider,
)

# =========================================================
# Application Logging
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("payment-service")

# Explicitly attach OpenTelemetry logging handler.
# Uvicorn may configure logging before this module is imported,
# which means logging.basicConfig() is not guaranteed to install
# our custom handler.
if otel_logging_handler not in logger.handlers:
    logger.addHandler(otel_logging_handler)

logger.setLevel(logging.INFO)


# =========================================================
# OpenTelemetry Tracing
# =========================================================

trace_provider = TracerProvider(
    resource=resource
)

otlp_trace_exporter = OTLPSpanExporter(
    endpoint="http://127.0.0.1:4318/v1/traces",
)

trace_provider.add_span_processor(
    BatchSpanProcessor(
        otlp_trace_exporter
    )
)

trace.set_tracer_provider(
    trace_provider
)

tracer = trace.get_tracer(
    "payment-service"
)


# =========================================================
# OpenTelemetry Metrics
# =========================================================

otlp_metric_exporter = OTLPMetricExporter(
    endpoint="http://127.0.0.1:4318/v1/metrics",
)

metric_reader = PeriodicExportingMetricReader(
    exporter=otlp_metric_exporter,
    export_interval_millis=5000,
)

meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[
        metric_reader
    ],
)

metrics.set_meter_provider(
    meter_provider
)

meter = metrics.get_meter(
    "payment-service"
)


# =========================================================
# Payment Metrics
# =========================================================

payment_requests = meter.create_counter(
    name="payment.requests",
    description="Total number of payment requests",
    unit="1",
)

payment_successes = meter.create_counter(
    name="payment.successes",
    description="Total number of successful payments",
    unit="1",
)

payment_failures = meter.create_counter(
    name="payment.failures",
    description="Total number of failed payments",
    unit="1",
)

payment_duration = meter.create_histogram(
    name="payment.duration",
    description="Payment processing duration",
    unit="s",
)


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="DevRescue Payment Service",
    version="0.1.0",
)


# =========================================================
# Health
# =========================================================

@app.get("/health")
def health():

    return {
        "service": "payment-service",
        "status": "healthy",
    }


# =========================================================
# Payment
# =========================================================

@app.post("/payments")
def process_payment(
    amount: float
):

    start_time = time.perf_counter()

    request_id = (
        f"req-{random.randint(10000, 99999)}"
    )

    payment_requests.add(1)

    with tracer.start_as_current_span(
        "process_payment"
    ) as span:

        span.set_attribute(
            "payment.amount",
            amount,
        )

        span.set_attribute(
            "payment.request_id",
            request_id,
        )

        logger.info(
            "payment_request request_id=%s amount=%s",
            request_id,
            amount,
        )

        # -------------------------------------------------
        # Simulated processing latency
        # -------------------------------------------------

        time.sleep(
            random.uniform(2.0, 3.0)
        )

        # -------------------------------------------------
        # Validation failure
        # -------------------------------------------------

        if amount <= 0:

            payment_failures.add(1)

            span.set_attribute(
                "payment.status",
                "failed",
            )

            span.set_status(
                Status(
                    StatusCode.ERROR,
                    "Invalid payment amount",
                )
            )

            logger.error(
                "invalid_payment request_id=%s amount=%s",
                request_id,
                amount,
            )

            duration = (
                time.perf_counter()
                - start_time
            )

            payment_duration.record(
                duration
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    "Payment amount must be "
                    "greater than zero."
                ),
            )

        # -------------------------------------------------
        # Successful payment
        # -------------------------------------------------

        span.set_attribute(
            "payment.status",
            "success",
        )

        span.set_status(
            Status(StatusCode.OK)
        )

        logger.info(
            "payment_success request_id=%s amount=%s",
            request_id,
            amount,
        )

        duration = (
            time.perf_counter()
            - start_time
        )

        payment_successes.add(1)

        payment_duration.record(
            duration
        )

        return {
            "request_id": request_id,
            "status": "success",
            "amount": amount,
        }