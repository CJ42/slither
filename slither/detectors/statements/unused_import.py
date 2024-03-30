from typing import List
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification, Output


class UnusedImport(AbstractDetector):
    """
    Detector unused imports.
    """

    ARGUMENT = "unused-import"
    HELP = "Detects unused imports"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-imports"

    WIKI_TITLE = "Unused Imports"
    WIKI_DESCRIPTION = "Importing a file that is not used in the contract likely indicates a mistake. The import should be removed until it is needed."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
    ```solidity
    import {A} from "./A.sol";
    contract B {}
    ```
    B either should import from A and it was forgotten or the import is not needed and should be removed.
    """
    # endregion wiki_exploit_scenario
    WIKI_RECOMMENDATION = (
        "Remove the unused import. If the import is needed later, it can be added back."
    )

    def _detect(self) -> List[Output]:
        results: List[Output] = []
        # This is computed lazily and then memoized so we need to trigger the computation.
        self.slither._compute_offsets_to_ref_impl_decl()

        for unit in self.slither.compilation_units:
            for filename, scope in unit.scopes.items():
                unused = []
                for i in scope.imports:
                    # `scope.imports` contains all transitive imports so we need to filter out imports not explicitly imported in the file.
                    # Otherwise, we would recommend removing an import that is used by a leaf contract and cause compilation errors.
                    if i.scope != scope:
                        continue

                    import_path = self.slither.crytic_compile.filename_lookup(i.filename)

                    use_found = False
                    # Search through all references to the imported file
                    for _, refs in self.slither._offset_to_references[import_path].items():
                        for ref in refs:
                            # If there is a reference in this file to the imported file, it is used.
                            if ref.filename == filename:
                                use_found = True
                                break

                        if use_found:
                            break

                    if not use_found:
                        unused.append(f"{i.source_mapping.content} ({i.source_mapping}")

                if len(unused) > 0:
                    unused_list = ""
                    for i in unused:
                        unused_list += f"\n\t-{i}"

                    results.append(
                        self.generate_result(
                            [
                                f"The following unused import(s) in {filename.used} should be removed: {unused_list}\n",
                            ]
                        )
                    )

        return results
