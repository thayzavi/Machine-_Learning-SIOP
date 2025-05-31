document.addEventListener('DOMContentLoaded', () => {
    // Definir datas padrão (últimos 30 dias)
    const inicio = new Date();
    const fim = new Date();
    inicio.setDate(inicio.getDate() - 30);
    document.getElementById('dataInicio').valueAsDate = inicio;
    document.getElementById('dataFim').valueAsDate = fim;
});

let dadosCasos = [];
let graficoRosca = null;
let graficoDistribuicao = null;
let graficoModelo = null;

const coresPalette = [
    '#40516c', '#e4d7dc', '#536878', '#5e1755',
    '#e08247', '#f88c51', '#a0a0a0'
];

async function carregarDados() {
    try {
        const res = await fetch("http://localhost:5000/api/casos");
        dadosCasos = await res.json();
        console.log("Dados carregados:", dadosCasos);
        atualizarGraficos();
        inicializarGraficoModelo();
    } catch (erro) {
        console.error("Erro ao carregar dados:", erro);
        alert("Não foi possível carregar os dados.");
    }
}

async function inicializarGraficoModelo() {
    try {
        const res = await fetch("http://localhost:5000/api/modelo/coeficientes");
        const data = await res.json();

        const processedData = {};
        Object.keys(data).forEach(key => {
            processedData[key] = Number(data[key]);
        });

        const sortedEntries = Object.entries(processedData)
            .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));

        const labels = sortedEntries.map(([key]) => key);
        const valores = sortedEntries.map(([, value]) => value);

        const ctx = document.createElement('canvas');
        document.getElementById("graficoModelo").innerHTML = '';
        document.getElementById("graficoModelo").appendChild(ctx);

        if (graficoModelo) graficoModelo.destroy();

        graficoModelo = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Importância',
                    data: valores,
                    backgroundColor: '#5d759c',
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error("Erro ao carregar ou renderizar o gráfico do modelo:", error);
    }
}

function filtrarPorData(casos) {
    const inicio = document.getElementById('dataInicio').value;
    const fim = document.getElementById('dataFim').value;

    return casos.filter(caso => {
        if (!caso.data_do_caso) return false;
        const data = new Date(caso.data_do_caso);
        const dataInicio = inicio ? new Date(inicio) : null;
        const dataFim = fim ? new Date(fim) : null;
        return (!dataInicio || data >= dataInicio) && (!dataFim || data <= dataFim);
    });
}

function atualizarGraficos() {
    const dadosFiltrados = filtrarPorData(dadosCasos);
    console.log("Dados filtrados:", dadosFiltrados);
    const variavel = document.getElementById("variavelRosa").value;
    atualizarGraficoRosca(dadosFiltrados, variavel);
    atualizarGraficoDistribuicao(dadosFiltrados);
}

function contarOcorrencias(dados, chave) {
    const contagem = {};
    dados.forEach(caso => {
        try {
            const valor = chave.includes('.')
                ? chave.split('.').reduce((o, k) => o && o[k], caso)
                : caso[chave];
            if (valor !== undefined && valor !== null) {
                contagem[valor] = (contagem[valor] || 0) + 1;
            }
        } catch { }
    });
    return contagem;
}

function atualizarGraficoRosca(dadosFiltrados, variavel = "tipo_do_caso") {
    const contagem = contarOcorrencias(dadosFiltrados, variavel);
    const labels = Object.keys(contagem);
    const valores = Object.values(contagem);
    const cores = coresPalette.slice(0, labels.length);

    const ctx = document.createElement('canvas');
    document.getElementById("graficoRosca").innerHTML = '';
    document.getElementById("graficoRosca").appendChild(ctx);

    if (graficoRosca) graficoRosca.destroy();

    graficoRosca = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: valores,
                backgroundColor: cores,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function atualizarGraficoDistribuicao(dadosFiltrados) {
    const idades = dadosFiltrados
        .map(c => c.vitima?.idade)
        .filter(i => typeof i === 'number' && !isNaN(i) && i > 0);

    const max = Math.max(...idades, 100);
    const bins = [];
    const labels = [];

    for (let i = 1; i <= max; i += 10) {
        labels.push(`${i}-${i + 9}`);
        bins.push(0);
    }

    idades.forEach(idade => {
        const index = Math.floor((idade - 1) / 10);
        if (index >= 0 && index < bins.length) bins[index]++;
    });

    const ctx = document.createElement('canvas');
    document.getElementById("graficoDistribuicao").innerHTML = '';
    document.getElementById("graficoDistribuicao").appendChild(ctx);

    if (graficoDistribuicao) graficoDistribuicao.destroy();

    graficoDistribuicao = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Número de vítimas',
                data: bins,
                backgroundColor: '#5d759c',
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Event listeners para filtros
document.getElementById("dataInicio").addEventListener("change", atualizarGraficos);
document.getElementById("dataFim").addEventListener("change", atualizarGraficos);
document.getElementById("variavelRosa").addEventListener("change", atualizarGraficos);

// Inicializar dados
carregarDados();
