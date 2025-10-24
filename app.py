import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, BooleanField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Optional

# --- Configuração ---
app = Flask(__name__)
# Chave secreta para segurança dos formulários (CSRF)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-dificil-de-adivinhar'
# Configuração do Banco de Dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'petshop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Inicialização das Extensões ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# --- Modelo do Banco de Dados ---
class Cachorro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(1), nullable=False) # 'M' ou 'F'
    proprietario = db.Column(db.String(100), nullable=False)
    
    classificacao = db.Column(db.String(50), default='')
    castrado = db.Column(db.Boolean, default=False)
    grau_energia = db.Column(db.String(1), nullable=False) # 'B', 'M', 'A'
    reativo_caes = db.Column(db.Boolean, default=False)
    reativo_pessoas = db.Column(db.Boolean, default=False)
    restricao_alimentos = db.Column(db.Text, default='')
    gosta_contato = db.Column(db.Boolean, default=True)
    responde_estimulos = db.Column(db.Boolean, default=True)

    frequencia_semanal = db.Column(db.Integer, default=1)
    passeia_na_praca = db.Column(db.Boolean, default=False)
    duracao_passeio = db.Column(db.Integer, default=30)
    grupo_passeio = db.Column(db.String(50), default='')
    enriquecimento_ambiental = db.Column(db.Boolean, default=False)
    atividade_mental = db.Column(db.Boolean, default=False)
    presencas = db.Column(db.Text, default='')

    def __repr__(self):
        return f'<Cachorro {self.nome}>'


# --- Formulário ---
class CachorroForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    data_nascimento = DateField('Data de Nascimento (AAAA-MM-DD)', validators=[DataRequired()])
    genero = SelectField('Gênero', choices=[('M', 'Macho'), ('F', 'Fêmea')], validators=[DataRequired()])
    proprietario = StringField('Proprietário', validators=[DataRequired()])
    classificacao = StringField('Classificação (Ex: Porte Pequeno, Raça)', validators=[Optional()])
    
    castrado = BooleanField('Castrado')
    grau_energia = SelectField('Grau de Energia', choices=[('B', 'Baixo'), ('M', 'Médio'), ('A', 'Alto')], validators=[DataRequired()])
    reativo_caes = BooleanField('Reativo a cães')
    reativo_pessoas = BooleanField('Reativo a pessoas')
    restricao_alimentos = TextAreaField('Restrição de Alimentos (Opcional)', validators=[Optional()])
    gosta_contato = BooleanField('Gosta de contato físico')
    responde_estimulos = BooleanField('Responde a estímulos (brinquedos, etc)')

    frequencia_semanal = IntegerField('Frequência Semanal (visitas)', validators=[DataRequired()])
    passeia_na_praca = BooleanField('Passeia na praça')
    duracao_passeio = IntegerField('Duração do Passeio (minutos)', validators=[DataRequired()])
    grupo_passeio = StringField('Grupo do Passeio (Opcional)', validators=[Optional()])
    enriquecimento_ambiental = BooleanField('Faz enriquecimento ambiental')
    atividade_mental = BooleanField('Faz atividade mental')
    presencas = TextAreaField('Registro de Presenças (Ex: 20/10, 22/10...)', validators=[Optional()])
    
    submit = SubmitField('Salvar')


# --- Rotas (Views) ---

# Rota para Listar todos os cachorros (READ) E PESQUISAR
@app.route('/')
def index():
    # Pega o termo de pesquisa da URL (ex: /?pesquisa=Avelã)
    query = request.args.get('Pesquisa', '') 
    
    if query:
        # Se houver uma pesquisa, filtra o banco de dados (ilike faz ser case-insensitive)
        # Busca por nome OU proprietário
        search_term = f'%{query}%'
        cachorros = Cachorro.query.filter(
            db.or_(
                Cachorro.nome.ilike(search_term),
                Cachorro.proprietario.ilike(search_term)
            )
        ).all()
    else:
        # Se não houver pesquisa, pega todos
        cachorros = Cachorro.query.all()
        
    # Passa a variável 'query' para o template para o input lembrar o que foi digitado
    return render_template('index.html', cachorros=cachorros, query=query)


# Rota para Adicionar um novo cachorro (CREATE)
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    form = CachorroForm()
    if form.validate_on_submit():
        novo_cachorro = Cachorro()
        form.populate_obj(novo_cachorro) # Popula o objeto com os dados do form
        db.session.add(novo_cachorro)
        db.session.commit()
        flash(f'Cachorro "{novo_cachorro.nome}" cadastrado com sucesso!', 'success')
        return redirect(url_for('index'))
    return render_template('form_cachorro.html', form=form, titulo='Adicionar Cachorro')

# Rota para Editar um cachorro (UPDATE)
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    cachorro = Cachorro.query.get_or_404(id)
    form = CachorroForm(obj=cachorro) # Preenche o form com dados existentes
    if form.validate_on_submit():
        # Atualiza os dados do objeto 'cachorro' com os dados do formulário
        form.populate_obj(cachorro)
        db.session.commit()
        flash(f'Dados do "{cachorro.nome}" atualizados!', 'success')
        return redirect(url_for('index'))
    
    # Se o formulário for carregado (GET) ou se for inválido (POST)
    return render_template('form_cachorro.html', form=form, titulo='Editar Cachorro')

# Rota para Deletar um cachorro (DELETE)
@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    cachorro = Cachorro.query.get_or_404(id)
    nome_cachorro = cachorro.nome
    db.session.delete(cachorro)
    db.session.commit()
    flash(f'Cachorro "{nome_cachorro}" removido com sucesso.', 'info')
    return redirect(url_for('index'))

