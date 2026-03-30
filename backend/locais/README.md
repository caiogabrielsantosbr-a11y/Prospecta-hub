# Pasta de Locais

Esta pasta contém arquivos JSON com listas de locais (cidades, estados, regiões) para extração no GMap.

## Formato do JSON

Cada arquivo JSON deve seguir este formato:

```json
{
  "nome": "Nome do Conjunto de Locais",
  "descricao": "Descrição opcional",
  "locais": [
    "São Paulo, SP",
    "Rio de Janeiro, RJ",
    "Belo Horizonte, MG"
  ]
}
```

## Exemplo

Veja o arquivo `brasil-capitais.json` como exemplo.

## Como usar

1. Crie um arquivo JSON nesta pasta seguindo o formato acima
2. A aplicação irá detectar automaticamente todos os arquivos JSON
3. Os locais estarão disponíveis na interface do GMap Extractor
