import { decryptDataSourceParams } from "../services/datasource";
import { runAthenaQuery } from "../services/athena";
import { AthenaConnectionParams } from "../../types/integrations/athena";
import { FormatDialect } from "../util/sql";
import { DataSourceProperties } from "../../types/datasource";
import { formatInformationSchema } from "../util/informationSchemas";
import { InformationSchema, RawInformationSchema } from "../types/Integration";
import SqlIntegration from "./SqlIntegration";

export default class Athena extends SqlIntegration {
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  params: AthenaConnectionParams;
  setParams(encryptedParams: string) {
    this.params = decryptDataSourceParams<AthenaConnectionParams>(
      encryptedParams
    );
  }
  getSourceProperties(): DataSourceProperties {
    return {
      ...super.getSourceProperties(),
      supportsInformationSchema: true,
    };
  }
  getFormatDialect(): FormatDialect {
    return "trino";
  }
  getSensitiveParamKeys(): string[] {
    return ["accessKeyId", "secretAccessKey"];
  }
  toTimestamp(date: Date) {
    return `from_iso8601_timestamp('${date.toISOString()}')`;
  }
  runQuery(sql: string) {
    return runAthenaQuery(this.params, sql);
  }
  addTime(
    col: string,
    unit: "hour" | "minute",
    sign: "+" | "-",
    amount: number
  ): string {
    return `${col} ${sign} INTERVAL '${amount}' ${unit}`;
  }
  formatDate(col: string): string {
    return `substr(to_iso8601(${col}),1,10)`;
  }
  dateDiff(startCol: string, endCol: string) {
    return `date_diff('day', ${startCol}, ${endCol})`;
  }
  useAliasInGroupBy(): boolean {
    return false;
  }
  ensureFloat(col: string): string {
    return `1.0*${col}`;
  }
  async getInformationSchema(): Promise<InformationSchema[]> {
    const sql = `SELECT
        table_name,
        table_catalog,
        table_schema,
        count(column_name) as column_count
      FROM
        information_schema.columns
      WHERE
        table_schema
      NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
      GROUP BY (table_name, table_schema, table_catalog)`;

    const results = await this.runQuery(sql);

    if (!results.length) {
      throw new Error(`No tables found.`);
    }

    return formatInformationSchema(results as RawInformationSchema[], "athena");
  }

  async getTableData(
    databaseName: string,
    tableSchema: string,
    tableName: string
  ): Promise<{ tableData: null | unknown[]; refreshMS: number }> {
    const sql = `SELECT
        data_type,
        column_name
      FROM
        information_schema.columns
      WHERE
        table_catalog
      IN ('${databaseName}')
      AND
        table_schema
      IN ('${tableSchema}')
      AND
        table_name
      IN ('${tableName}')`;

    const queryStartTime = Date.now();
    const tableData = await this.runQuery(sql);
    const queryEndTime = Date.now();

    return { tableData, refreshMS: queryEndTime - queryStartTime };
  }
}
