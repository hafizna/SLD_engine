"""Ingestion: turn an evidence source into ObservedObject / ObservedConnection.

The structured-observation import (`save_observation_batch`) is the contract that
every adapter -- vision parser, vector PDF/SVG parser, Excel importer, and
eventually the NMM/CIM adapter -- must produce. Nothing downstream cares which
adapter produced it.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import ObservedConnection, ObservedObject, SourceDocument
from app.services.reconciliation import normalize_name


class VisionExtractor:
    """Placeholder for a screenshot / vision model extractor."""

    def extract(self, file_path: str):
        raise NotImplementedError("Plug in a vector-PDF parser or vision model here")


def save_observation_batch(db: Session, batch) -> SourceDocument:
    doc = SourceDocument(
        filename=batch.filename,
        document_type=batch.document_type,
        analytical_hint=batch.analytical_hint,
        source_ref=getattr(batch, "source_ref", None),
        effective_date=batch.effective_date,
    )
    db.add(doc)
    db.flush()

    by_external: dict[str, ObservedObject] = {}
    for item in batch.objects:
        obs = ObservedObject(
            document_id=doc.id,
            external_key=item.external_key,
            object_type=item.object_type.upper(),
            raw_label=item.raw_label,
            normalized_name=normalize_name(item.raw_label),
            site_name=item.site_name,
            voltage_hv_kv=item.voltage_hv_kv,
            voltage_lv_kv=item.voltage_lv_kv,
            unit_no=item.unit_no,
            tier_hint=getattr(item, "tier_hint", None),
            status_hint=getattr(item, "status_hint", None),
            confidence=item.confidence,
        )
        db.add(obs)
        db.flush()
        if item.external_key:
            by_external[item.external_key] = obs

    for c in batch.connections:
        a = by_external.get(c.from_external_key)
        b = by_external.get(c.to_external_key)
        if not a or not b:
            raise ValueError(f"Unknown endpoint: {c.from_external_key}->{c.to_external_key}")
        db.add(ObservedConnection(
            document_id=doc.id,
            from_observed_id=a.id,
            to_observed_id=b.id,
            relation_type=c.relation_type,
            circuit_type_hint=getattr(c, "circuit_type_hint", None),
            status_hint=getattr(c, "status_hint", None),
            confidence=c.confidence,
        ))

    db.commit()
    return doc
