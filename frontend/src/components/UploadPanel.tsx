import { type FormEvent, useRef, useState } from "react";

type UploadPanelProps = {
  onImport: (file: File) => Promise<void>;
  loading: boolean;
  maxUploadSizeMb: number;
};

export function UploadPanel({
  onImport,
  loading,
  maxUploadSizeMb,
}: UploadPanelProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      return;
    }
    await onImport(selectedFile);
    setSelectedFile(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  return (
    <section className="panel panel-upload">
      <div className="panel-kicker">Entrada de dados</div>
      <div className="panel-header">
        <div>
          <h2>Importe um CSV para persistir a analise</h2>
          <p>
            O arquivo vai gerar importacao, transacoes categorizadas, snapshot
            de relatorio e uma fila de revisao para o analista.
          </p>
        </div>
        <button
          className="ghost-button"
          type="button"
          onClick={() => inputRef.current?.click()}
        >
          Escolher arquivo
        </button>
      </div>

      <form className="upload-form" onSubmit={handleSubmit}>
        <label className={`dropzone ${selectedFile ? "is-filled" : ""}`}>
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            onChange={(event) => {
              const file = event.target.files?.[0] ?? null;
              setSelectedFile(file);
            }}
          />
          <span className="dropzone-pill">CSV financeiro</span>
          <strong>{selectedFile?.name ?? "Arraste ou selecione o arquivo"}</strong>
          <span>
            Limite atual de upload: {maxUploadSizeMb} MB. A melhor experiencia
            agora e trabalhar com arquivos exportados do banco ou ERP em CSV.
          </span>
        </label>

        <div className="upload-actions">
          <div className="upload-hint">
            Depois do upload, voce ja cai na mesa de revisao para ajustar
            categorias e fechar o relatorio.
          </div>
          <button className="primary-button" type="submit" disabled={!selectedFile || loading}>
            {loading ? "Importando..." : "Importar e abrir revisao"}
          </button>
        </div>
      </form>
    </section>
  );
}
