// Function to load JSON data
async function loadJsonData(filePath) {
    const response = await fetch(filePath);
    const data = await response.json();
    return data;
}

// Variable to store the selected stock's token
let selectedStockToken = null;

// Variables for Supertrend
let supertrendLength = 10; // Default value
let supertrendFactor = 3;  // Default value

// Variables for order form
let selectedTradingSymbol = null;
let selectedSymbolToken = null;

// Function to search for stock details
function searchStock() {
    const searchInput = document.getElementById('stockSearch').value.trim();
    const instrumentType = document.getElementById('instrumentType').value;

    // Extract the stock name and symbol from the input
    const [stockName, stockSymbol] = extractNameAndSymbol(searchInput);

    if (!stockName && !stockSymbol) {
        alert("Please enter a stock name or symbol.");
        return;
    }

    const results = {
        EQ: [],
        FUT: [],
        OPT: [],
        Others: []
    };

    data.forEach(instrument => {
        const matchesName = stockName ? instrument.name.toUpperCase().includes(stockName.toUpperCase()) : true;
        const matchesSymbol = stockSymbol ? instrument.symbol.toUpperCase().includes(stockSymbol.toUpperCase()) : true;

        if (matchesName && matchesSymbol) {
            if (instrumentType === "") {
                if (instrument.symbol.includes('-EQ')) {
                    results.EQ.push({ name: instrument.name, symbol: instrument.symbol, token: instrument.token });
                } else if (instrument.symbol.includes('FUT')) {
                    results.FUT.push({ name: instrument.name, symbol: instrument.symbol, token: instrument.token });
                } else if (instrument.symbol.endsWith('PE') || instrument.symbol.endsWith('CE')) {
                    results.OPT.push({ name: instrument.name, symbol: instrument.symbol, token: instrument.token });
                } else {
                    results.Others.push({ name: instrument.name, symbol: instrument.symbol, token: instrument.token });
                }
            } else if (instrumentType === "EQ" && instrument.symbol.includes('-EQ')) {
                results.EQ.push({ name: instrument.name, symbol: instrument.symbol, token: instrument.token });
            } else if (instrumentType === "FUT" && instrument.symbol.includes('FUT')) {
                results.FUT.push({ name: instrument.name, symbol: instrument.symbol, token: instrument.token });
            } else if (instrumentType === "OPT" && (instrument.symbol.endsWith('PE') || instrument.symbol.endsWith('CE'))) {
                results.OPT.push({ name: instrument.name, symbol: instrument.symbol, token: instrument.token });
            }
        }
    });

    const resultLabel = document.getElementById('resultLabel');
    resultLabel.innerHTML = '';

    const displayResults = (type, header) => {
        if (results[type].length > 0) {
            const typeHeader = document.createElement('h3');
            typeHeader.textContent = header;
            resultLabel.appendChild(typeHeader);
            results[type].forEach(stock => {
                const resultItem = document.createElement('div');
                resultItem.textContent = `Name: ${stock.name}, Symbol: ${stock.symbol}, Token: ${stock.token}`;
                resultItem.style.cursor = 'pointer';
                resultItem.classList.add('search-result-item');
                resultItem.addEventListener('click', () => {
                    // Update the search bar with the selected stock's name and symbol
                    document.getElementById('stockSearch').value = `${stock.name} (${stock.symbol})`;
                    // Store the trading symbol and token
                    selectedTradingSymbol = stock.symbol;
                    selectedSymbolToken = stock.token;
                    
                    // Display the stock name and symbol
                    displaySelectedStock(stock.name, stock.symbol);
                    
                    // Enable the order form
                    enableOrderForm();
                    
                    console.log('Selected Stock:', {
                        name: stock.name,
                        symbol: selectedTradingSymbol,
                        token: selectedSymbolToken
                    });
                });
                resultLabel.appendChild(resultItem);
            });
        }
    };

    if (instrumentType === "") {
        displayResults('EQ', 'Equities');
        displayResults('FUT', 'Futures');
        displayResults('OPT', 'Options');
        displayResults('Others', 'Others');
    } else if (instrumentType === "EQ") {
        displayResults('EQ', 'Equities');
    } else if (instrumentType === "FUT") {
        displayResults('FUT', 'Futures');
    } else if (instrumentType === "OPT") {
        displayResults('OPT', 'Options');
    }

    if (results.EQ.length === 0 && results.FUT.length === 0 && results.OPT.length === 0 && results.Others.length === 0) {
        resultLabel.textContent = "No results found.";
    }
}

// Function to extract name and symbol from the input
function extractNameAndSymbol(input) {
    const match = input.match(/^(.*?)\s*\((.*?)\)$/); // Match "Name (Symbol)"
    if (match) {
        return [match[1].trim(), match[2].trim()]; // Return [name, symbol]
    }
    return [input.trim(), null]; // Return [name, null] if no symbol is found
}

// Load the JSON data
const filePath = 'OpenAPIScripMaster.json'; // Path to the JSON file
let data = [];

loadJsonData(filePath).then(loadedData => {
    data = loadedData;
    document.getElementById('searchButton').addEventListener('click', searchStock);
}).catch(error => {
    console.error('Error loading JSON data:', error);
});

// Login functionality
document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    document.getElementById('loginContainer').style.display = 'none';
    document.getElementById('dashboardContainer').style.display = 'block';
});

// Function to update autocomplete suggestions
function updateSuggestions() {
    const searchQuery = document.getElementById('stockSearch').value.trim().toUpperCase();
    const instrumentType = document.getElementById('instrumentType').value;
    const datalist = document.getElementById('stockSuggestions');
    datalist.innerHTML = ''; // Clear previous suggestions

    if (!searchQuery) return; // Exit if search query is empty

    // Filter data based on search query and instrument type
    const filteredData = data.filter(instrument => {
        const matchesQuery = instrument.symbol.toUpperCase().includes(searchQuery) || instrument.name.toUpperCase().includes(searchQuery);
        const matchesType = instrumentType === "" || 
                            (instrumentType === "EQ" && instrument.symbol.includes('-EQ')) ||
                            (instrumentType === "FUT" && instrument.symbol.includes('FUT')) ||
                            (instrumentType === "OPT" && (instrument.symbol.endsWith('PE') || instrument.symbol.endsWith('CE')));
        return matchesQuery && matchesType;
    });

    // Add filtered suggestions to the datalist
    filteredData.forEach(instrument => {
        const option = document.createElement('option');
        option.value = `${instrument.name} (${instrument.symbol})`; // Display name and symbol
        datalist.appendChild(option);
    });
}

// Event listeners for autocomplete
document.getElementById('stockSearch').addEventListener('input', updateSuggestions);
document.getElementById('instrumentType').addEventListener('change', updateSuggestions);

// Function to display the selected stock name and symbol in big words in the middle
function displaySelectedStock(stockName, stockSymbol) {
    const resultLabel = document.getElementById('resultLabel');
    resultLabel.innerHTML = ''; // Clear previous results

    // Create a div to display the selected stock name and symbol in big words
    const selectedStockDisplay = document.createElement('div');
    selectedStockDisplay.innerHTML = `
        <div style="font-size: 2rem; text-align: center; margin-top: 20px;">${stockName}</div>
        <div style="font-size: 1.5rem; text-align: center; margin-top: 10px;">${stockSymbol}</div>
    `;
    resultLabel.appendChild(selectedStockDisplay);
}

// Function to handle stock selection
function handleStockSelection() {
    const searchInput = document.getElementById('stockSearch').value.trim();
    const [stockName, stockSymbol] = extractNameAndSymbol(searchInput);

    if (!stockName) {
        return;
    }

    const selectedStock = data.find(instrument => {
        const matchesName = instrument.name.toUpperCase() === stockName.toUpperCase();
        const matchesSymbol = stockSymbol ? instrument.symbol.toUpperCase() === stockSymbol.toUpperCase() : true;
        return matchesName && matchesSymbol;
    });

    if (selectedStock) {
        // Store the trading symbol and token
        selectedTradingSymbol = selectedStock.symbol;
        selectedSymbolToken = selectedStock.token;
        
        // Display the stock name and symbol
        displaySelectedStock(selectedStock.name, selectedStock.symbol);
        
        // Enable the order form
        enableOrderForm();
        
        console.log('Selected Stock:', {
            name: selectedStock.name,
            symbol: selectedTradingSymbol,
            token: selectedSymbolToken
        });
    } else {
        searchStock();
    }
}

// Add event listener for stock selection
document.getElementById('stockSearch').addEventListener('change', handleStockSelection);

// Function to enable/disable order form
function enableOrderForm() {
    const orderForm = document.getElementById('orderForm');
    const orderButton = orderForm.querySelector('.order-button');
    
    if (selectedTradingSymbol && selectedSymbolToken) {
        orderButton.disabled = false;
        console.log('Order form enabled for:', selectedTradingSymbol);
    } else {
        orderButton.disabled = true;
        console.log('Order form disabled - no stock selected');
    }
}

// Function to handle order submission
async function handleOrderSubmit(event) {
    event.preventDefault();
    
    console.log('Order submission attempted with:', {
        symbol: selectedTradingSymbol,
        token: selectedSymbolToken
    });
    
    if (!selectedTradingSymbol || !selectedSymbolToken) {
        alert('Please select a stock first');
        return;
    }

    const orderData = {
        variety: "NORMAL",
        tradingsymbol: selectedTradingSymbol,
        symboltoken: selectedSymbolToken,
        transactiontype: document.getElementById('transactionType').value,
        exchange: "NSE",
        ordertype: document.getElementById('orderType').value,
        producttype: document.getElementById('productType').value,
        duration: document.getElementById('duration').value,
        stoploss: document.getElementById('stopLoss').value,
        quantity: document.getElementById('quantity').value
    };

    console.log('Submitting order with data:', orderData);

    try {
        const response = await fetch('/place_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(orderData)
        });

        const result = await response.json();
        console.log('Server response:', result);
        
        if (response.ok) {
            alert('Order placed successfully!');
            // Reset form
            event.target.reset();
        } else {
            alert('Failed to place order: ' + (result.message || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error placing order:', error);
        alert('Error placing order: ' + error.message);
    }
}

// Add event listener for order form submission
document.addEventListener('DOMContentLoaded', function() {
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        orderForm.addEventListener('submit', handleOrderSubmit);
    }
});

// Function to handle Supertrend calculation
function handleSupertrendCalculation() {
    const lengthInput = document.getElementById('stLength');
    const factorInput = document.getElementById('stFactor');
    
    // Get and validate the input values
    const length = parseInt(lengthInput.value);
    const factor = parseFloat(factorInput.value);
    
    if (isNaN(length) || isNaN(factor)) {
        alert('Please enter valid numbers for Length and Factor');
        return;
    }
    
    // Store the values in our variables
    supertrendLength = length;
    supertrendFactor = factor;
    
    // Display the values in the supertrend display area
    const supertrendDisplay = document.getElementById('supertrendDisplay');
    supertrendDisplay.innerHTML = `
        <p>Supertrend Parameters:</p>
        <p>Length: ${supertrendLength}</p>
        <p>Factor: ${supertrendFactor}</p>
    `;
    
    console.log('Supertrend Parameters:', { length: supertrendLength, factor: supertrendFactor });
    
    // Here you can add your supertrend calculation logic
    // calculateSupertrend(supertrendLength, supertrendFactor);
}

// Add event listener for the Apply Supertrend button
document.addEventListener('DOMContentLoaded', function() {
    const applySupertrendButton = document.getElementById('applySupertrend');
    if (applySupertrendButton) {
        applySupertrendButton.addEventListener('click', handleSupertrendCalculation);
    }
});
