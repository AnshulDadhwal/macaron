# Copyright (c) 2024 - 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/.

"""This module adds a Check that checks whether the provenance is verified."""
import logging

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from macaron.database.table_definitions import CheckFacts
from macaron.slsa_analyzer.analyze_context import AnalyzeContext
from macaron.slsa_analyzer.checks.base_check import BaseCheck
from macaron.slsa_analyzer.checks.check_result import CheckResultData, CheckResultType, Confidence, JustificationType
from macaron.slsa_analyzer.registry import registry
from macaron.slsa_analyzer.slsa_req import ReqName

logger: logging.Logger = logging.getLogger(__name__)


class ProvenanceVerifiedFacts(CheckFacts):
    """The ORM mapping for justifications in the provenance verified check."""

    __tablename__ = "_provenance_verified_check"

    #: The primary key.
    id: Mapped[int] = mapped_column(ForeignKey("_check_facts.id"), primary_key=True)  # noqa: A003

    #: The verified status of the provenance.
    verified: Mapped[str] = mapped_column(String, nullable=True, info={"justification": JustificationType.TEXT})

    __mapper_args__ = {
        "polymorphic_identity": __tablename__,
    }


class ProvenanceVerifiedCheck(BaseCheck):
    """This Check checks whether the provenance is flagged as verified in the context."""

    def __init__(self) -> None:
        """Initialize instance."""
        check_id = "mcn_provenance_verified_1"
        description = "Check whether the provenance is verified."
        depends_on: list[tuple[str, CheckResultType]] = []
        eval_reqs = [ReqName.EXPECTATION]
        super().__init__(
            check_id=check_id,
            description=description,
            depends_on=depends_on,
            eval_reqs=eval_reqs,
            result_on_skip=CheckResultType.FAILED,
        )

    def run_check(self, ctx: AnalyzeContext) -> CheckResultData:
        """Implement the check in this method.

        Parameters
        ----------
        ctx : AnalyzeContext
            The object containing processed data for the target repo.

        Returns
        -------
        CheckResultData
            The result of the check.
        """
        verified = ctx.dynamic_data["provenance_verified"]
        return CheckResultData(
            result_tables=[
                ProvenanceVerifiedFacts(
                    verified=f"The provenance is {'verified' if verified else 'not verified'}.",
                    confidence=Confidence.HIGH,
                )
            ],
            result_type=CheckResultType.PASSED if verified else CheckResultType.FAILED,
        )


registry.register(ProvenanceVerifiedCheck())
