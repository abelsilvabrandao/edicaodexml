from flask import Flask, request, render_template, redirect, url_for, send_file
import xml.etree.ElementTree as ET
import base64
from io import BytesIO

app = Flask(__name__)

# Função para analisar o XML e extrair os dados
def parse_xml(xml_str):
    try:
        root = ET.fromstring(xml_str)
        namespace = "http://www.portalfiscal.inf.br/nfe"

        nNF_element = root.find('.//{{{0}}}nNF'.format(namespace))
        emit_CNPJ_element = root.find('.//{{{0}}}emit/{{{0}}}CNPJ'.format(namespace))
        emit_xNome_element = root.find('.//{{{0}}}emit/{{{0}}}xNome'.format(namespace))  # Novo
        dest_CNPJ_element = root.find('.//{{{0}}}dest/{{{0}}}CNPJ'.format(namespace))
        dest_xNome_element = root.find('.//{{{0}}}dest/{{{0}}}xNome'.format(namespace))  # Novo
        vProd_element = root.find('.//{{{0}}}vProd'.format(namespace))
        vNF_element = root.find('.//{{{0}}}vNF'.format(namespace))

        if nNF_element is None:
            raise ValueError("Elemento 'nNF' não encontrado")

        nNF = nNF_element.text
        emit_CNPJ = emit_CNPJ_element.text if emit_CNPJ_element is not None else ''
        emit_xNome = emit_xNome_element.text if emit_xNome_element is not None else ''  # Novo
        dest_CNPJ = dest_CNPJ_element.text if dest_CNPJ_element is not None else ''
        dest_xNome = dest_xNome_element.text if dest_xNome_element is not None else ''  # Novo
        vProd = vProd_element.text if vProd_element is not None else ''
        vNF = vNF_element.text if vNF_element is not None else ''

        produtos = []

        for produto in root.findall('.//{{{0}}}det'.format(namespace)):
            cProd_element = produto.find('.//{{{0}}}cProd'.format(namespace))
            xProd_element = produto.find('.//{{{0}}}xProd'.format(namespace))
            uCom_element = produto.find('.//{{{0}}}uCom'.format(namespace))
            qCom_element = produto.find('.//{{{0}}}qCom'.format(namespace))
            vUnCom_element = produto.find('.//{{{0}}}vUnCom'.format(namespace))
            vTotal_element = produto.find('.//{{{0}}}vProd'.format(namespace))

            if None in (cProd_element, xProd_element, uCom_element, qCom_element, vUnCom_element, vTotal_element):
                raise ValueError("Um ou mais elementos de produto não encontrados")

            cProd = cProd_element.text
            xProd = xProd_element.text
            uCom = uCom_element.text
            qCom = qCom_element.text
            vUnCom = vUnCom_element.text
            vTotal = vTotal_element.text

            produtos.append({'cProd': cProd, 'xProd': xProd, 'uCom': uCom, 'qCom': qCom, 'vUnCom': vUnCom, 'vTotal': vTotal})

        return nNF, emit_CNPJ, emit_xNome, dest_CNPJ, dest_xNome, produtos, vProd, vNF
    except Exception as e:
        raise ValueError(f"Erro ao analisar o XML: {str(e)}")

# Função para modificar o XML conforme os dados fornecidos
def modify_xml(xml_str, data):
    try:
        root = ET.fromstring(xml_str)
        namespace = "http://www.portalfiscal.inf.br/nfe"

        # Modificar os elementos do XML conforme os dados fornecidos
        # Exemplo de modificação: Alterar o valor do elemento emit_xNome
        emit_xNome_element = root.find('.//{{{0}}}emit/{{{0}}}xNome'.format(namespace))
        if emit_xNome_element is not None:
            emit_xNome_element.text = data['emit_xNome']

        # Converter o XML modificado de volta para uma string
        modified_xml_str = ET.tostring(root, encoding='utf-8').decode()

        return modified_xml_str
    except Exception as e:
        raise ValueError(f"Erro ao modificar o XML: {str(e)}")

@app.route('/')
def upload_form():
    return render_template('index.html')

@app.route('/processar-xml', methods=['POST'])
def process_xml():
    try:
        xml_file = request.files['xml_file']
        if xml_file.filename == '':
            return 'Nenhum arquivo selecionado', 400

        xml_str = xml_file.read().decode('utf-8')
        xml_str_base64 = base64.b64encode(xml_str.encode()).decode('utf-8')

        return redirect(url_for('edit_xml_page', xml_str=xml_str_base64))
    except Exception as e:
        return f"Erro ao processar o XML: {str(e)}", 500

@app.route('/edit-xml-page', methods=['GET', 'POST'])
def edit_xml_page():
    if request.method == 'GET':
        try:
            xml_str_base64 = request.args.get('xml_str')
            if xml_str_base64 is None:
                return "Erro: XML não fornecido", 400

            xml_str = base64.b64decode(xml_str_base64).decode('utf-8')
            nNF, emit_CNPJ, emit_xNome, dest_CNPJ, dest_xNome, produtos, vProd, vNF = parse_xml(xml_str)

            return render_template('edit_xml.html', nNF=nNF, emit_CNPJ=emit_CNPJ, emit_xNome=emit_xNome, dest_CNPJ=dest_CNPJ, dest_xNome=dest_xNome, produtos=produtos, vProd=vProd, vNF=vNF, xml_saved=False)
        except Exception as e:
            return f"Erro ao abrir o XML para edição: {str(e)}", 500
    elif request.method == 'POST':
        try:
            xml_str = request.form['xml_data']
            if xml_str is None:
                return "Erro: XML não fornecido", 400

            # Modifica o XML conforme os dados fornecidos
            modified_xml_str = modify_xml(xml_str, request.form)

            return render_template('edit_xml.html', xml_data=modified_xml_str, xml_saved=True)
        except Exception as e:
            return f"Erro ao salvar o XML: {str(e)}", 500

@app.route('/download-xml')
def download_xml():
    filename = 'temp.xml'
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
