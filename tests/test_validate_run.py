import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_run.py"
VALID_FIXTURE = ROOT / "tests" / "fixtures" / "valid-run"
MISSING_FIXTURE = ROOT / "tests" / "fixtures" / "invalid-missing-artifacts"


class ValidateRunTests(unittest.TestCase):
    maxDiff = None

    def run_validator(self, run_dir: Path, stage: str | None = None):
        command = [sys.executable, str(VALIDATOR), str(run_dir)]
        if stage is not None:
            command.extend(["--stage", stage])
        return subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def copy_fixture(
        self,
        destination: Path,
        artifacts=None,
        run_id: str = "valid-run",
    ) -> Path:
        run_dir = destination / run_id
        run_dir.mkdir()
        selected = artifacts or [path.name for path in VALID_FIXTURE.iterdir()]
        for artifact in selected:
            shutil.copy2(VALID_FIXTURE / artifact, run_dir / artifact)
            if run_id != "valid-run":
                path = run_dir / artifact
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "valid-run", run_id
                    ),
                    encoding="utf-8",
                )
        return run_dir

    @staticmethod
    def load_json(run_dir: Path, artifact: str):
        return json.loads((run_dir / artifact).read_text(encoding="utf-8"))

    @staticmethod
    def write_json(run_dir: Path, artifact: str, data):
        (run_dir / artifact).write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )

    def convert_to_refresh(self, run_dir: Path, source_run_id: str):
        request_path = run_dir / "REQUEST.md"
        request = request_path.read_text(encoding="utf-8")
        request = request.replace("- Mode: `full`", "- Mode: `refresh`")
        request = request.replace(
            "- Refresh source run: `none`",
            f"- Refresh source run: `{source_run_id}`",
        )
        request_path.write_text(request, encoding="utf-8")
        for artifact in ("RAW_CONFERENCES.json", "NORMALIZED_CONFERENCES.json"):
            data = self.load_json(run_dir, artifact)
            data["run_metadata"]["mode"] = "refresh"
            data["run_metadata"]["source_run_id"] = source_run_id
            self.write_json(run_dir, artifact, data)
        additions = {
            "ENTITY_RESOLUTION.md": (
                "\n## Refresh Differences\n\n- No synthetic changes.\n"
            ),
            "QUALITY_REPORT.md": (
                "\n## Refresh Differences\n\n- No synthetic changes.\n"
            ),
            "REPORT.md": "\n## Refresh Changes\n\n- No synthetic changes.\n",
        }
        for artifact, addition in additions.items():
            path = run_dir / artifact
            text = path.read_text(encoding="utf-8")
            text = text.replace("- Mode: `full`", "- Mode: `refresh`")
            path.write_text(text + addition, encoding="utf-8")

    def test_valid_complete_fixture_passes_with_default_stage(self):
        result = self.run_validator(VALID_FIXTURE)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stage complete", result.stdout)

    def test_all_explicit_stages_pass(self):
        for stage in ("discovery", "raw", "normalized", "complete"):
            with self.subTest(stage=stage):
                result = self.run_validator(VALID_FIXTURE, stage)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_stage_requires_only_its_artifacts(self):
        stage_artifacts = {
            "discovery": [
                "REQUEST.md",
                "AGGREGATORS.md",
                "CONFERENCE_SOURCES.md",
            ],
            "raw": [
                "REQUEST.md",
                "AGGREGATORS.md",
                "CONFERENCE_SOURCES.md",
                "RAW_CONFERENCES.json",
            ],
            "normalized": [
                "REQUEST.md",
                "AGGREGATORS.md",
                "CONFERENCE_SOURCES.md",
                "RAW_CONFERENCES.json",
                "NORMALIZED_CONFERENCES.json",
                "ENTITY_RESOLUTION.md",
                "QUALITY_REPORT.md",
            ],
        }
        for stage, artifacts in stage_artifacts.items():
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temp:
                run_dir = self.copy_fixture(Path(temp), artifacts)
                result = self.run_validator(run_dir, stage)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_artifacts_fixture_fails(self):
        result = self.run_validator(MISSING_FIXTURE)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AGGREGATORS.md: required artifact is missing", result.stderr)
        self.assertIn("REPORT.md: required artifact is missing", result.stderr)

    def test_request_authorization_literal_must_match_exactly(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(
                Path(temp),
                ["REQUEST.md", "AGGREGATORS.md", "CONFERENCE_SOURCES.md"],
            )
            request_path = run_dir / "REQUEST.md"
            request_path.write_text(
                request_path.read_text(encoding="utf-8").replace(
                    "Authorization basis: `intentionally-public`",
                    "Authorization basis: `not-intentionally-public`",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir, "discovery")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("attendee authorization", result.stderr)

    def test_request_requires_timestamp_domains_and_completed_sections(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(
                Path(temp),
                ["REQUEST.md", "AGGREGATORS.md", "CONFERENCE_SOURCES.md"],
            )
            request_path = run_dir / "REQUEST.md"
            request = request_path.read_text(encoding="utf-8")
            request = request.replace(
                "- Request recorded at: `2026-09-22T00:00:00Z`\n", ""
            )
            request = request.replace(
                "- Required domains or publishers: example.invalid\n", ""
            )
            request = request.replace("## User Constraints", "## Constraints")
            request_path.write_text(request, encoding="utf-8")

            result = self.run_validator(run_dir, "discovery")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required request field 'recorded at'", result.stderr)
        self.assertIn("Required domains or publishers", result.stderr)
        self.assertIn("required section 'User Constraints'", result.stderr)

    def test_duplicate_declared_id_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["organizations"].append(
                copy.deepcopy(normalized["organizations"][0])
            )
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate ID O001", result.stderr)

    def test_unresolved_foreign_key_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["organizer_ids"] = ["O999"]
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unresolved foreign key 'O999'", result.stderr)

    def test_unresolved_field_provenance_source_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["field_provenance"]["/canonical_name"][
                "source_ids"
            ] = ["S999"]
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unresolved source reference 'S999'", result.stderr)

    def test_unresolved_field_provenance_pointer_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            provenance = normalized["conferences"][0]["field_provenance"]
            provenance["/missing_field"] = provenance.pop("/canonical_name")
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "field provenance pointer does not resolve within the normalized record",
            result.stderr,
        )

    def test_material_field_without_provenance_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            del normalized["conferences"][0]["field_provenance"]["/start_date"]
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "material field '/start_date' lacks field-level provenance",
            result.stderr,
        )

    def test_provenance_must_point_to_matching_raw_branch(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["field_provenance"]["/start_date"][
                "raw_artifact_pointers"
            ] = [
                "/conferences/0/branches/identity_and_aliases/raw_values/0"
            ]
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "provenance for '/start_date' must point to branch "
            "'dates_times_timezone_recurrence_and_status'",
            result.stderr,
        )

    def test_normalized_attendance_value_must_match_raw_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["attendee_records_or_aggregates"][0][
                "aggregate_count"
            ] = 999
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "aggregate count of 42", "aggregate count of 999"
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "aggregate_count: normalized value 999 is not supported by its raw "
            "artifact provenance",
            result.stderr,
        )

    def test_normalized_person_role_must_match_raw_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["people"][0][
                "public_professional_role"
            ] = "Chief Executive Officer"
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "synthetic program chair", "chief executive officer"
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "public_professional_role: normalized value 'Chief Executive Officer' "
            "is not supported by its raw artifact provenance",
            result.stderr,
        )

    def test_normalized_person_role_cannot_append_unsupported_role(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["people"][0]["public_professional_role"] = (
                "Program Chair and Chief Executive Officer"
            )
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "synthetic program chair",
                    "program chair and chief executive officer",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "public_professional_role: normalized value 'Program Chair and "
            "Chief Executive Officer' is not supported by its raw artifact "
            "provenance",
            result.stderr,
        )

    def test_normalized_scope_cannot_append_unsupported_registration_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["attendee_records_or_aggregates"][0]["scope"] = (
                "prior synthetic edition. Registration was sold out."
            )
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "scope: normalized value 'prior synthetic edition. Registration "
            "was sold out.' is not supported by its raw artifact provenance",
            result.stderr,
        )

    def test_normalized_identity_cannot_append_unsupported_edition(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["canonical_name"] = (
                "Synthetic Validation Conference — Fabricated Executive Edition"
            )
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            report_path = run_dir / "REPORT.md"
            report = report_path.read_text(encoding="utf-8").replace(
                "Synthetic Validation Conference",
                "Synthetic Validation Conference — Fabricated Executive Edition",
            )
            report_path.write_text(report, encoding="utf-8")

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "canonical_name: normalized value 'Synthetic Validation Conference "
            "— Fabricated Executive Edition' is not supported by its raw "
            "artifact provenance",
            result.stderr,
        )

    def test_raw_identity_evidence_must_support_normalized_value(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            identity = raw["conferences"][0]["branches"][
                "identity_and_aliases"
            ]["raw_values"][0]
            identity["raw_text"] = "Fabricated Conference Name"
            identity["observed_value"]["name"] = "Fabricated Conference Name"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "canonical_name: normalized value 'Synthetic Validation Conference' "
            "is not supported by its raw artifact provenance",
            result.stderr,
        )

    def test_raw_attendance_evidence_must_support_normalized_value(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            attendee = raw["conferences"][0]["branches"][
                "attendees_and_attendance"
            ]["raw_values"][0]
            attendee["raw_text"] = (
                "The prior synthetic edition recorded 999 attendees."
            )
            attendee["observed_value"]["aggregate_count"] = 999
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "aggregate_count: normalized value 42 is not supported by its raw "
            "artifact provenance",
            result.stderr,
        )

    def test_guessed_public_contact_cannot_reuse_unrelated_raw_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            person = normalized["people"][0]
            person["business_contacts"].append(
                {
                    "contact_type": "business-email",
                    "value": "casey.guessed@example.invalid",
                    "authorization_basis": {
                        "basis": "intentionally-public",
                        "description": (
                            "The source explicitly publishes this business email."
                        ),
                        "source_ids": ["S001"],
                        "authorization_record": None,
                    },
                    "source_ids": ["S001"],
                }
            )
            person["field_provenance"]["/business_contacts/0"] = {
                "source_ids": ["S001"],
                "raw_artifact_pointers": [
                    "/conferences/0/branches/people_and_public_contacts/"
                    "raw_values/0"
                ],
                "note": "Adversarial guessed contact.",
            }
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "business_contacts/0/value: normalized value "
            "'casey.guessed@example.invalid' is not supported by its raw "
            "artifact provenance",
            result.stderr,
        )

    def test_structured_contact_value_must_appear_in_raw_text(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            raw_person = raw["conferences"][0]["branches"][
                "people_and_public_contacts"
            ]["raw_values"][0]
            raw_person["observed_value"][
                "business_email"
            ] = "casey@example.invalid"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            person = normalized["people"][0]
            person["business_contacts"].append(
                {
                    "contact_type": "business-email",
                    "value": "casey@example.invalid",
                    "authorization_basis": {
                        "basis": "intentionally-public",
                        "description": (
                            "The source explicitly publishes this business email."
                        ),
                        "source_ids": ["S001"],
                        "authorization_record": None,
                    },
                    "source_ids": ["S001"],
                }
            )
            person["field_provenance"]["/business_contacts/0"] = {
                "source_ids": ["S001"],
                "raw_artifact_pointers": [
                    "/conferences/0/branches/people_and_public_contacts/"
                    "raw_values/0"
                ],
                "note": "Adversarial structured-only contact.",
            }
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "contact value 'casey@example.invalid' is absent from raw_text",
            result.stderr,
        )

    def test_normalized_value_from_not_published_branch_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["topics"] = ["unsupported"]
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "value cannot be present when branch "
            "'description_themes_topics_type_and_languages' has status "
            "'not-published'",
            result.stderr,
        )

    def test_bad_collection_status_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(
                Path(temp),
                [
                    "REQUEST.md",
                    "AGGREGATORS.md",
                    "CONFERENCE_SOURCES.md",
                    "RAW_CONFERENCES.json",
                ],
            )
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            raw["conferences"][0]["branches"]["identity_and_aliases"][
                "collection_status"
            ] = "unknown"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)

            result = self.run_validator(run_dir, "raw")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid collection status 'unknown'", result.stderr)

    def test_public_only_raw_individual_attendee_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(
                Path(temp),
                [
                    "REQUEST.md",
                    "AGGREGATORS.md",
                    "CONFERENCE_SOURCES.md",
                    "RAW_CONFERENCES.json",
                ],
            )
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            attendee_value = raw["conferences"][0]["branches"][
                "attendees_and_attendance"
            ]["raw_values"][0]
            attendee_value["observed_value"] = {
                "record_type": "individual-record",
                "name": "Jordan Example",
            }
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)

            result = self.run_validator(run_dir, "raw")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "public-only mode cannot contain individual attendee records",
            result.stderr,
        )

    def test_retained_value_with_unresolved_authorization_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(
                Path(temp),
                [
                    "REQUEST.md",
                    "AGGREGATORS.md",
                    "CONFERENCE_SOURCES.md",
                    "RAW_CONFERENCES.json",
                ],
            )
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            authorization = raw["conferences"][0]["branches"][
                "people_and_public_contacts"
            ]["raw_values"][0]["authorization_basis"]
            authorization["basis"] = "unresolved"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)

            result = self.run_validator(run_dir, "raw")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "retained value cannot use an unclear or denied authorization basis",
            result.stderr,
        )

    def test_unresolved_report_citation_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "[S001]", "[S999]", 1
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unresolved report citation [S999]", result.stderr)

    def test_aggregator_citation_outside_listing_coverage_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "- Identity: Synthetic Validation Conference. [S001]",
                    "- Identity: Synthetic Validation Conference. [S001] [A001]",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "aggregator citation [A001] appears outside the observed-listing",
            result.stderr,
        )

    def test_ineligible_direct_source_cannot_support_facts_or_report(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            for source in (raw["sources"][0], normalized["sources"][1]):
                source["review_state"] = "inaccessible"
                source["extraction_eligibility"] = "ineligible"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not reviewed and eligible for factual use", result.stderr)
        self.assertIn("direct source citation [S001]", result.stderr)

    def test_source_claims_must_cover_each_supported_branch(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            source_path = run_dir / "CONFERENCE_SOURCES.md"
            source_path.write_text(
                source_path.read_text(encoding="utf-8").replace(
                    "identity, dates, official-url, organizers, people, attendance, "
                    "provenance, confidence, contradictions",
                    "identity",
                ),
                encoding="utf-8",
            )
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            raw["sources"][0]["supported_fields_or_claims"] = ["identity"]
            normalized["sources"][1]["supported_fields_or_claims"] = ["identity"]
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "does not declare support for claim 'dates'",
            result.stderr,
        )
        self.assertIn(
            "does not declare support for report claim 'organizers'",
            result.stderr,
        )

    def test_source_cannot_claim_an_unsupported_branch(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            source_path = run_dir / "CONFERENCE_SOURCES.md"
            source_path.write_text(
                source_path.read_text(encoding="utf-8").replace(
                    "attendance, provenance",
                    "attendance, venue, provenance",
                ),
                encoding="utf-8",
            )
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            raw["sources"][0]["supported_fields_or_claims"].insert(-3, "venue")
            normalized["sources"][1]["supported_fields_or_claims"].insert(
                -3, "venue"
            )
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "declares claim 'venue', but branch 'venue' has no retained evidence",
            result.stderr,
        )

    def test_source_summary_cannot_claim_unextracted_contact(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            summary = (
                "The synthetic page identifies the conference, organizer, "
                "Casey's public business email, and a prior-edition aggregate "
                "attendance count."
            )
            source_path = run_dir / "CONFERENCE_SOURCES.md"
            source_path.write_text(
                re.sub(
                    r"(?m)^- Bounded excerpt or faithful summary: .+$",
                    f"- Bounded excerpt or faithful summary: {summary}",
                    source_path.read_text(encoding="utf-8"),
                ),
                encoding="utf-8",
            )
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            raw["sources"][0]["bounded_excerpt_or_faithful_summary"] = summary
            normalized["sources"][1][
                "bounded_excerpt_or_faithful_summary"
            ] = summary
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "summary claims public contact data without extracted contact evidence",
            result.stderr,
        )

    def test_source_publication_date_must_match_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            raw["sources"][0]["publication_or_update_date"] = "2000-01-01"
            normalized["sources"][1]["publication_or_update_date"] = "2000-01-01"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "publication_or_update_date",
            result.stderr,
        )

    def test_source_limitations_must_match_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            source_path = run_dir / "CONFERENCE_SOURCES.md"
            source_path.write_text(
                source_path.read_text(encoding="utf-8").replace(
                    "Limitations: Synthetic test evidence only.",
                    "Limitations: Different limitation.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "limitations: values do not exactly match CONFERENCE_SOURCES.md",
            result.stderr,
        )

    def test_aggregator_listing_url_must_match_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["sources"][0][
                "public_url"
            ] = "https://different.example.invalid/listing"
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "does not match AGGREGATORS.md",
            result.stderr,
        )

    def test_related_venue_cannot_bypass_not_published_branch(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["venues"].append(
                {
                    "id": "V001",
                    "canonical_name": "Unsupported Venue",
                    "aliases": [],
                    "venue_type": None,
                    "postal_address": None,
                    "locality": None,
                    "administrative_area": None,
                    "country": None,
                    "postal_code": None,
                    "latitude": None,
                    "longitude": None,
                    "official_website": None,
                    "public_telephone": None,
                    "public_email": None,
                    "public_contact_page": None,
                    "public_map_url": None,
                    "rooms_or_buildings": [],
                    "accessibility_notes": [],
                    "transport_notes": [],
                    "conference_relationships": [
                        {
                            "conference_id": "C001",
                            "relationship": "unsupported synthetic relationship",
                            "start_date": None,
                            "end_date": None,
                            "source_ids": ["S001"],
                        }
                    ],
                    "collection_status": "complete",
                    "source_ids": ["S001"],
                    "field_provenance": {
                        "/canonical_name": {
                            "source_ids": ["S001"],
                            "raw_artifact_pointers": [
                                "/conferences/0/branches/identity_and_aliases/raw_values/0"
                            ],
                            "note": "Adversarial test value.",
                        },
                        "/conference_relationships/0": {
                            "source_ids": ["S001"],
                            "raw_artifact_pointers": [
                                "/conferences/0/branches/identity_and_aliases/raw_values/0"
                            ],
                            "note": "Adversarial test relationship.",
                        },
                    },
                }
            )
            normalized["quality_metrics"]["entity_counts"]["venues"] = 1
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "but branch 'venue' has status 'not-published'",
            result.stderr,
        )

    def test_quality_report_missing_required_section_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "## Entity Counts", "## Counts", 1
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "required section 'Entity Counts' is missing or empty",
            result.stderr,
        )

    def test_quality_report_missing_required_subsection_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "### Unresolved Foreign Keys",
                    "### Foreign Keys",
                    1,
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "required subsection 'Unresolved Foreign Keys'",
            result.stderr,
        )

    def test_failed_privacy_check_and_blocking_warning_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["quality_metrics"]["attendee_privacy_checks"][0][
                "result"
            ] = "fail"
            normalized["quality_metrics"]["blocking_warnings"] = [
                "Synthetic privacy blocker."
            ]
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "completed validation requires 'pass'",
            result.stderr,
        )
        self.assertIn(
            "cannot pass with blocking warnings",
            result.stderr,
        )

    def test_quality_report_entity_counts_match_json(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "| Conferences | 1 |",
                    "| Conferences | 999 |",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Entity Counts row 'Conferences' records 999, expected 1",
            result.stderr,
        )

    def test_quality_report_requires_both_artifact_result_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "| `RAW_CONFERENCES.json` | pass | Synthetic fixture conforms "
                    "to the raw schema. |\n",
                    "",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "must contain a passing row for RAW_CONFERENCES.json",
            result.stderr,
        )

    def test_quality_report_branch_coverage_matches_json(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality = quality_path.read_text(encoding="utf-8")
            quality = re.sub(
                r"(?ms)^## Branch Coverage\n.*?(?=^## Source-Class Coverage)",
                "## Branch Coverage\n\n- Complete: venue only.\n\n",
                quality,
            )
            quality_path.write_text(quality, encoding="utf-8")

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Branch Coverage is missing row 'Identity and aliases'",
            result.stderr,
        )

    def test_quality_report_source_coverage_matches_json(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality = quality_path.read_text(encoding="utf-8")
            quality = re.sub(
                r"(?ms)^## Source-Class Coverage\n.*?"
                r"(?=^## Conferences Without Official Sources)",
                "## Source-Class Coverage\n\n"
                "- No direct sources support extraction.\n\n",
                quality,
            )
            quality_path.write_text(quality, encoding="utf-8")

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Source-Class Coverage is missing required columns",
            result.stderr,
        )

    def test_quality_report_collection_gaps_match_json(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality = quality_path.read_text(encoding="utf-8")
            quality = re.sub(
                r"(?ms)^## Inaccessible Sources and Collection Gaps\n.*?"
                r"(?=^## Blocking Warnings)",
                "## Inaccessible Sources and Collection Gaps\n\n"
                "- Collection gaps: none.\n\n",
                quality,
            )
            quality_path.write_text(quality, encoding="utf-8")

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Inaccessible Sources and Collection Gaps is missing required columns",
            result.stderr,
        )

    def test_quality_report_failed_privacy_result_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "No individual attendee or private registration data is "
                    "present: pass.",
                    "No individual attendee or private registration data is "
                    "present: fail.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "contains a failed or not-run check",
            result.stderr,
        )

    def test_quality_report_translation_counts_match_json(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "- Translation records: 0.",
                    "- Translation records: 999.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "quality summary field 'Translation records' records 999, expected 0",
            result.stderr,
        )

    def test_quality_report_requires_each_authorization_check(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "- Aggregate attendance evidence is intentionally public: pass.\n",
                    "",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "is missing required result 'Aggregate attendance evidence is "
            "intentionally public: pass.'",
            result.stderr,
        )

    def test_quality_report_empty_json_sections_must_state_none(self):
        mutations = (
            (
                "### Unresolved Foreign Keys\n\n- None.",
                "### Unresolved Foreign Keys\n\n- C999 is unresolved.",
                "Unresolved Foreign Keys",
            ),
            (
                "### Unresolved Source References\n\n- None.",
                "### Unresolved Source References\n\n- S999 is unresolved.",
                "Unresolved Source References",
            ),
            (
                "## Conferences Without Official Sources\n\n- None.",
                "## Conferences Without Official Sources\n\n"
                "- C001 has no official source.",
                "Conferences Without Official Sources",
            ),
            (
                "## Conflicts\n\n- None.",
                "## Conflicts\n\n- C001 has an unresolved date conflict.",
                "Conflicts",
            ),
        )
        for original, replacement, heading in mutations:
            with self.subTest(heading=heading), tempfile.TemporaryDirectory() as temp:
                run_dir = self.copy_fixture(Path(temp))
                quality_path = run_dir / "QUALITY_REPORT.md"
                quality_path.write_text(
                    quality_path.read_text(encoding="utf-8").replace(
                        original, replacement
                    ),
                    encoding="utf-8",
                )

                result = self.run_validator(run_dir)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                f"section '{heading}' must state only 'None'",
                result.stderr,
            )

    def test_quality_report_privacy_narrative_cannot_contradict_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "- No individual attendee or private registration data is "
                    "present: pass.",
                    "- No individual attendee or private registration data is "
                    "present: pass; private registration data is also present.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "contains unrecognized or contradictory result",
            result.stderr,
        )

    def test_quality_conflicts_must_derive_from_conference_contradictions(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["quality_metrics"]["conflicts"] = [
                {
                    "json_pointer": "/conferences/0/start_date",
                    "values": ["2099-06-15", "2099-07-01"],
                    "source_ids": ["S001"],
                    "resolution": "unresolved",
                }
            ]
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "## Conflicts\n\n- None.",
                    "## Conflicts\n\n- C001 has an unresolved date conflict.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "quality_metrics/conflicts: values must exactly match conference "
            "contradiction records",
            result.stderr,
        )

    def test_quality_report_gap_narrative_matches_json(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "The synthetic source does not publish venue data. | "
                    "not-published | Use `Insufficient evidence`.",
                    "Venue is fully confirmed. | not-published | Publish venue "
                    "as fact.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("description does not match JSON", result.stderr)
        self.assertIn(
            "reporting effect must require Insufficient evidence",
            result.stderr,
        )

    def test_quality_report_cannot_hide_blocking_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            quality_path = run_dir / "QUALITY_REPORT.md"
            quality_path.write_text(
                quality_path.read_text(encoding="utf-8").replace(
                    "## Blocking Warnings\n\n- None.",
                    "## Blocking Warnings\n\n- Synthetic blocker.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Blocking Warnings must state only 'None'",
            result.stderr,
        )

    def test_quality_metrics_require_artifact_results(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["quality_metrics"]["artifact_schema_results"] = []
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "must contain results for RAW_CONFERENCES.json and "
            "NORMALIZED_CONFERENCES.json",
            result.stderr,
        )

    def test_report_requires_conference_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report = report_path.read_text(encoding="utf-8")
            report = re.sub(
                r"(?ms)^## Conference Comparison\n.*?(?=^## Conference Summaries)",
                "",
                report,
            )
            report_path.write_text(report, encoding="utf-8")

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "required section 'Conference Comparison'",
            result.stderr,
        )

    def test_report_material_claim_requires_supported_citation(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "- Collection status: Unsupported branches are marked "
                    "`not-published`.",
                    "- Venue: Unsupported Palace.\n"
                    "- Collection status: Unsupported branches are marked "
                    "`not-published`.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "material 'venue' claim in conference summary C001 lacks a direct "
            "source citation",
            result.stderr,
        )

    def test_report_summary_identity_matches_normalized_data(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "- Identity: Synthetic Validation Conference. [S001]",
                    "- Identity: Fabricated Conference Name. [S001]",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "conference summary C001 identity statement does not match "
            "normalized data",
            result.stderr,
        )

    def test_report_summary_organizer_matches_normalized_data(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "- Organizer: Synthetic Conference Organization. [S001]",
                    "- Organizer: Fabricated Organizer. [S001]",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "conference summary C001 organizers statement does not match "
            "normalized data",
            result.stderr,
        )

    def test_report_summary_identity_rejects_appended_fabrication(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "- Identity: Synthetic Validation Conference. [S001]",
                    "- Identity: Synthetic Validation Conference, also Fabricated "
                    "Conference Name. [S001]",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "identity statement contains unsupported narrative or values",
            result.stderr,
        )

    def test_report_summary_dates_reject_extra_date(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "- Dates: 2099-06-15. [S001]",
                    "- Dates: 2099-06-15 and 2099-07-01. [S001]",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "dates statement contains unsupported dates ['2099-07-01']",
            result.stderr,
        )

    def test_report_summary_people_role_matches_normalized_data(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "Casey Example is listed as a synthetic program chair.",
                    "Casey Example is listed as a chief executive officer.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "people statement does not match the normalized role",
            result.stderr,
        )

    def test_report_summary_people_rejects_appended_role(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "synthetic program chair.",
                    "synthetic program chair and chief executive officer.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "people statement contains unsupported role narrative",
            result.stderr,
        )

    def test_report_summary_dates_reject_natural_language_extra_date(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "- Dates: 2099-06-15. [S001]",
                    "- Dates: 2099-06-15 and July 1, 2099. [S001]",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "dates statement contains unsupported dates ['2099-07-01']",
            result.stderr,
        )

    def test_report_summary_attendance_rejects_registration_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "this does not prove current attendance.",
                    "this does not prove current attendance, and registration "
                    "was sold out.",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "attendance statement contains unsupported registration content",
            result.stderr,
        )

    def test_report_summary_attendance_rejects_extra_count(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "aggregate count of 42;",
                    "aggregate counts of 42 and 999;",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "attendance statement contains unsupported numeric values",
            result.stderr,
        )

    def test_comparison_populated_column_requires_branch_and_claim_support(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "| Synthetic Validation Conference | 2099-06-15 | "
                    "Insufficient evidence | Insufficient evidence |",
                    "| Synthetic Validation Conference | 2099-06-15 | "
                    "Insufficient evidence | Unsupported Palace |",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "column 'Venue' is populated while branch 'venue' has status "
            "'not-published'",
            result.stderr,
        )
        self.assertIn(
            "column 'Venue' lacks a cited source supporting claim 'venue'",
            result.stderr,
        )

    def test_comparison_value_must_match_normalized_data(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "| Synthetic Validation Conference | 2099-06-15 |",
                    "| Synthetic Validation Conference | 2099-06-16 |",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "column 'Dates' value '2099-06-16' does not match normalized data",
            result.stderr,
        )

    def test_report_source_index_must_include_all_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "| S001 | Synthetic Validation Conference | "
                    "official-conference | "
                    "https://conference.example.invalid/ | 2026-09-22 |\n",
                    "",
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Source Index IDs do not match normalized source records",
            result.stderr,
        )

    def test_refresh_requires_existing_source_run(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            request_path = run_dir / "REQUEST.md"
            request = request_path.read_text(encoding="utf-8")
            request = request.replace("- Mode: `full`", "- Mode: `refresh`")
            request = request.replace(
                "- Refresh source run: `none`",
                "- Refresh source run: `missing-source-run`",
            )
            request_path.write_text(request, encoding="utf-8")
            for artifact in ("RAW_CONFERENCES.json", "NORMALIZED_CONFERENCES.json"):
                data = self.load_json(run_dir, artifact)
                data["run_metadata"]["mode"] = "refresh"
                data["run_metadata"]["source_run_id"] = "missing-source-run"
                self.write_json(run_dir, artifact, data)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "refresh source run directory",
            result.stderr,
        )

    def test_refresh_requires_report_comparison_section(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.copy_fixture(root, run_id="source-run")
            run_dir = self.copy_fixture(root)
            request_path = run_dir / "REQUEST.md"
            request = request_path.read_text(encoding="utf-8")
            request = request.replace("- Mode: `full`", "- Mode: `refresh`")
            request = request.replace(
                "- Refresh source run: `none`",
                "- Refresh source run: `source-run`",
            )
            request_path.write_text(request, encoding="utf-8")
            for artifact in ("RAW_CONFERENCES.json", "NORMALIZED_CONFERENCES.json"):
                data = self.load_json(run_dir, artifact)
                data["run_metadata"]["mode"] = "refresh"
                data["run_metadata"]["source_run_id"] = "source-run"
                self.write_json(run_dir, artifact, data)
            for artifact in ("ENTITY_RESOLUTION.md", "QUALITY_REPORT.md"):
                path = run_dir / artifact
                path.write_text(
                    path.read_text(encoding="utf-8")
                    + "\n## Refresh Differences\n\n- No synthetic changes.\n",
                    encoding="utf-8",
                )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "refresh mode requires a nonempty 'Refresh Changes' section",
            result.stderr,
        )

    def test_refresh_source_run_must_validate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source_run = self.copy_fixture(root, run_id="source-run")
            (source_run / "NORMALIZED_CONFERENCES.json").write_text(
                '{"artifact": "NORMALIZED_CONFERENCES.json",',
                encoding="utf-8",
            )
            run_dir = self.copy_fixture(root)
            self.convert_to_refresh(run_dir, "source-run")

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "refresh source run 'source-run' is invalid",
            result.stderr,
        )
        self.assertIn("invalid JSON", result.stderr)

    def test_refresh_scope_must_match_source_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.copy_fixture(root, run_id="source-run")
            run_dir = self.copy_fixture(root)
            self.convert_to_refresh(run_dir, "source-run")
            request_path = run_dir / "REQUEST.md"
            request_path.write_text(
                request_path.read_text(encoding="utf-8").replace(
                    "Validate one synthetic conference record through the "
                    "complete harness workflow.",
                    "Find unrelated marine-biology conferences.",
                ),
                encoding="utf-8",
            )
            for artifact in ("RAW_CONFERENCES.json", "NORMALIZED_CONFERENCES.json"):
                data = self.load_json(run_dir, artifact)
                data["run_metadata"][
                    "objective"
                ] = "Find unrelated marine-biology conferences."
                self.write_json(run_dir, artifact, data)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "refresh request scope differs from source run 'source-run' in: "
            "objective",
            result.stderr,
        )

    def test_refresh_no_change_claim_must_match_actual_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.copy_fixture(root, run_id="source-run")
            run_dir = self.copy_fixture(root)
            self.convert_to_refresh(run_dir, "source-run")
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            date_value = raw["conferences"][0]["branches"][
                "dates_times_timezone_recurrence_and_status"
            ]["raw_values"][0]
            date_value["raw_text"] = "16 June 2099"
            date_value["observed_value"]["start_date"] = "2099-06-16"
            date_value["observed_value"]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["start_date"] = "2099-06-16"
            normalized["conferences"][0]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "2099-06-15", "2099-06-16"
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "claims no changes, but normalized data differs from the source run",
            result.stderr,
        )

    def test_refresh_change_none_is_treated_as_no_change_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.copy_fixture(root, run_id="source-run")
            run_dir = self.copy_fixture(root)
            self.convert_to_refresh(run_dir, "source-run")
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            date_value = raw["conferences"][0]["branches"][
                "dates_times_timezone_recurrence_and_status"
            ]["raw_values"][0]
            date_value["raw_text"] = "16 June 2099"
            date_value["observed_value"]["start_date"] = "2099-06-16"
            date_value["observed_value"]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["start_date"] = "2099-06-16"
            normalized["conferences"][0]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            for artifact in (
                "ENTITY_RESOLUTION.md",
                "QUALITY_REPORT.md",
                "REPORT.md",
            ):
                path = run_dir / artifact
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "No synthetic changes.", "Change: none."
                    ),
                    encoding="utf-8",
                )
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "2099-06-15", "2099-06-16"
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "claims no changes, but normalized data differs from the source run",
            result.stderr,
        )

    def test_refresh_detects_source_metadata_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.copy_fixture(root, run_id="source-run")
            run_dir = self.copy_fixture(root)
            self.convert_to_refresh(run_dir, "source-run")
            ledger_path = run_dir / "CONFERENCE_SOURCES.md"
            ledger_path.write_text(
                ledger_path.read_text(encoding="utf-8").replace(
                    "Publication or update date: 2099-01-01",
                    "Publication or update date: 2099-02-01",
                ),
                encoding="utf-8",
            )
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            raw["sources"][0]["publication_or_update_date"] = "2099-02-01"
            normalized["sources"][1][
                "publication_or_update_date"
            ] = "2099-02-01"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "claims no changes, but normalized data differs from the source run",
            result.stderr,
        )

    def test_refresh_description_must_identify_actual_changed_field(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.copy_fixture(root, run_id="source-run")
            run_dir = self.copy_fixture(root)
            self.convert_to_refresh(run_dir, "source-run")
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            date_value = raw["conferences"][0]["branches"][
                "dates_times_timezone_recurrence_and_status"
            ]["raw_values"][0]
            date_value["raw_text"] = "16 June 2099"
            date_value["observed_value"]["start_date"] = "2099-06-16"
            date_value["observed_value"]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["start_date"] = "2099-06-16"
            normalized["conferences"][0]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            for artifact in (
                "ENTITY_RESOLUTION.md",
                "QUALITY_REPORT.md",
                "REPORT.md",
            ):
                path = run_dir / artifact
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "No synthetic changes.",
                        "Change: Sponsor removed from C001.",
                    ),
                    encoding="utf-8",
                )
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "2099-06-15", "2099-06-16"
                ),
                encoding="utf-8",
            )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "does not identify the actual changed field or collection",
            result.stderr,
        )

    def test_refresh_description_rejects_wrong_resulting_value(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.copy_fixture(root, run_id="source-run")
            run_dir = self.copy_fixture(root)
            self.convert_to_refresh(run_dir, "source-run")
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            date_value = raw["conferences"][0]["branches"][
                "dates_times_timezone_recurrence_and_status"
            ]["raw_values"][0]
            date_value["raw_text"] = "16 June 2099"
            date_value["observed_value"]["start_date"] = "2099-06-16"
            date_value["observed_value"]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["start_date"] = "2099-06-16"
            normalized["conferences"][0]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "2099-06-15", "2099-06-16"
                ),
                encoding="utf-8",
            )
            for artifact in (
                "ENTITY_RESOLUTION.md",
                "QUALITY_REPORT.md",
                "REPORT.md",
            ):
                path = run_dir / artifact
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "No synthetic changes.",
                        "Change: Date moved to 2099-06-15.",
                    ),
                    encoding="utf-8",
                )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "mentions a previous value without the actual current value",
            result.stderr,
        )

    def test_refresh_description_cannot_reassert_previous_value_as_current(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.copy_fixture(root, run_id="source-run")
            run_dir = self.copy_fixture(root)
            self.convert_to_refresh(run_dir, "source-run")
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            date_value = raw["conferences"][0]["branches"][
                "dates_times_timezone_recurrence_and_status"
            ]["raw_values"][0]
            date_value["raw_text"] = "16 June 2099"
            date_value["observed_value"]["start_date"] = "2099-06-16"
            date_value["observed_value"]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            normalized["conferences"][0]["start_date"] = "2099-06-16"
            normalized["conferences"][0]["end_date"] = "2099-06-16"
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)
            report_path = run_dir / "REPORT.md"
            report_path.write_text(
                report_path.read_text(encoding="utf-8").replace(
                    "2099-06-15", "2099-06-16"
                ),
                encoding="utf-8",
            )
            for artifact in (
                "ENTITY_RESOLUTION.md",
                "QUALITY_REPORT.md",
                "REPORT.md",
            ):
                path = run_dir / artifact
                path.write_text(
                    path.read_text(encoding="utf-8").replace(
                        "No synthetic changes.",
                        "Change: Date moved to 2099-06-16, but the actual current "
                        "date remains 2099-06-15.",
                    ),
                    encoding="utf-8",
                )

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "presents a previous value as the current result",
            result.stderr,
        )

    def test_entity_resolution_summary_uses_schema_vocabulary(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            path = run_dir / "ENTITY_RESOLUTION.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace("| Rejected candidate |", "| Reject |")
            text = text.replace("| Unresolved candidate |", "| Unresolved |")
            path.write_text(text, encoding="utf-8")

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Decision Summary is missing row 'Rejected candidate'",
            result.stderr,
        )

    def test_public_only_attendee_authorization_violation_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            authorization = normalized["attendee_records_or_aggregates"][0][
                "authorization_basis"
            ]
            authorization["basis"] = "user-authorized-input"
            authorization["authorization_record"] = "synthetic-user-input"
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "public-only mode requires intentionally-public evidence",
            result.stderr,
        )

    def test_intentionally_public_description_cannot_be_negated(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            authorization = normalized["attendee_records_or_aggregates"][0][
                "authorization_basis"
            ]
            authorization["description"] = (
                "Guessed from social activity; not intentionally published."
            )
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "intentionally-public authorization cannot be guessed",
            result.stderr,
        )

    def test_intentionally_public_description_cannot_be_derived_or_unpublished(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            normalized = self.load_json(run_dir, "NORMALIZED_CONFERENCES.json")
            description = (
                "Never published; derived from social activity on an official page."
            )
            raw["conferences"][0]["branches"]["attendees_and_attendance"][
                "raw_values"
            ][0]["authorization_basis"]["description"] = description
            normalized["attendee_records_or_aggregates"][0][
                "authorization_basis"
            ]["description"] = description
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)
            self.write_json(run_dir, "NORMALIZED_CONFERENCES.json", normalized)

            result = self.run_validator(run_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "intentionally-public authorization cannot be guessed",
            result.stderr,
        )

    def test_run_id_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(Path(temp))
            raw = self.load_json(run_dir, "RAW_CONFERENCES.json")
            raw["run_metadata"]["run_id"] = "different-run"
            self.write_json(run_dir, "RAW_CONFERENCES.json", raw)

            result = self.run_validator(run_dir, "raw")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match REQUEST.md 'valid-run'", result.stderr)

    def test_invalid_json_fails_with_location(self):
        with tempfile.TemporaryDirectory() as temp:
            run_dir = self.copy_fixture(
                Path(temp),
                [
                    "REQUEST.md",
                    "AGGREGATORS.md",
                    "CONFERENCE_SOURCES.md",
                    "RAW_CONFERENCES.json",
                ],
            )
            (run_dir / "RAW_CONFERENCES.json").write_text(
                '{"artifact": "RAW_CONFERENCES.json",',
                encoding="utf-8",
            )

            result = self.run_validator(run_dir, "raw")

        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(
            result.stderr,
            r"RAW_CONFERENCES\.json#/[0-9]+:[0-9]+: invalid JSON",
        )


if __name__ == "__main__":
    unittest.main()
