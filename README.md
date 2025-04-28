# Recipe Builder - Agentic AI POC

A simple Proof of Concept (POC) for building recipes using an agentic AI model.

## Getting Started

Follow these steps to set up and run the project on your local machine.

### 1. Clone the repo

```
git clone https://github.com/poonamvebuin/Recipie-Builder-Agentic-AI-POC

cd Recipie-Builder-Agentic-AI-POC
```

### 2. Create a Virtual Environment

Create and activate a virtual environment for dependency isolation.

```
python -m venv env
env\Scripts\activate
```

### 3. Set OpenAI API Key

Set your OpenAI API key in the terminal session:

```
set OPENAI_API_KEY=your_openai_key_here
```

### 4. Install Dependencies

Install all required libraries from the `requirements.txt` file:

```
pip install -r requirements.txt
```

### 5. Configure Environment

Add your database credentials to the `.env` file in the project root.

### 6. Install pgvector

Make sure PostgreSQL is installed and running before you proceed. 
Follow the steps given in the repo `https://github.com/pgvector/pgvector` to install pgvector extension in PostgreSql.

Once installation done, enable the extension (do this once in each database where you want to use it)

```
CREATE EXTENSION vector;
```

### 7. Create table "products" 

Create table ai.products with below query in the database

```
CREATE TABLE ai.products (
	product_id serial4 NOT NULL,
	product_name varchar(255) NOT NULL,
	price varchar(100) NOT NULL,
	stock_quantity int4 NOT NULL,
	weight int4 NULL,
	unit varchar(10) NULL,
	brand varchar(100) NULL,
	expiry_date date NULL,
	is_vegan bool DEFAULT false NULL,
	created_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	updated_at timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	tax varchar(100) NULL,
	category varchar(100) NULL,
	CONSTRAINT products_pkey PRIMARY KEY (product_id)
);
```

Now, export data from the given csv file named products inside Databse folder for this table.



### 8. Run the Application

Launch the Streamlit app:

```
streamlit run app.py
```