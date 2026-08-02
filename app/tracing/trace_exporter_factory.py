from app.config_models.tracing_config import TracingConfig
from app.io.file_text_writer import FileTextWriter
from app.tracing.exporters.base_trace_exporter import (
    BaseTraceExporter,
)
from app.tracing.exporters.composite_trace_exporter import (
    CompositeTraceExporter,
)
from app.tracing.exporters.json_trace_exporter import (
    JsonTraceExporter,
)
from app.tracing.exporters.logging_trace_exporter import (
    LoggingTraceExporter,
)
from app.tracing.serializers.trace_event_serializer import (
    TraceEventSerializer,
)


class TraceExporterFactory:
    def create(
        self,
        config: TracingConfig,
    ) -> BaseTraceExporter:
        exporters: list[BaseTraceExporter] = []

        if config.enable_logging:
            exporters.append(
                LoggingTraceExporter(),
            )

        if config.json_file_path is not None:
            exporters.append(
                JsonTraceExporter(
                    serializer=TraceEventSerializer(),
                    writer=FileTextWriter(
                        file_path=config.json_file_path,
                    ),
                )
            )

        if len(exporters) == 1:
            return exporters[0]

        return CompositeTraceExporter(
            exporters=exporters,
        )
