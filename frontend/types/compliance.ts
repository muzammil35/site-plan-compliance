export interface ExtractedField {
  value: number | null;
  unit: string;
  confidence: number;
  note: string;
}

export interface ExtractedData {
  lot_width: ExtractedField;
  lot_depth: ExtractedField;
  lot_area: ExtractedField;
  building_width: ExtractedField;
  building_depth: ExtractedField;
  building_area: ExtractedField;
  front_setback: ExtractedField;
  rear_setback: ExtractedField;
  side_setback_left: ExtractedField;
  side_setback_right: ExtractedField;
  building_height: ExtractedField;
  parking_spaces: ExtractedField;
  lot_coverage?: ExtractedField;
}

export interface ComplianceResult {
  rule_key: string;
  label: string;
  required: string;
  actual: string | null;
  status: "PASS" | "FAIL" | "UNKNOWN";
  confidence: number;
  note: string;
  deficiency: number | null;
}

export interface AnalysisResponse {
  extracted: ExtractedData;
  compliance: ComplianceResult[];
  annotated_pdf: string | null;
  summary: {
    total: number;
    pass: number;
    fail: number;
    unknown: number;
  };
}
