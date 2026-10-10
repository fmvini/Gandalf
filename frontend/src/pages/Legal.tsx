import { useEffect, useRef, type ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { legalContact, legalLinks, legalUpdatedAt, type LegalKind } from '../lib/legal'

type LegalSection = { id: string; title: string; content: ReactNode }
type LegalDocument = { title: string; introduction: string; sections: LegalSection[] }

const lgpdUrl = 'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm'
const cookiesGuideUrl = 'https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia_orientativo_cookies_e_protecao_de_dados_pessoais'

function Contact() {
  return <p>Responsável pelo Gandalf: <strong>{legalContact.name}</strong>. Para dúvidas, solicitações sobre seus dados ou problemas com o serviço, escreva para <a href={'mailto:' + legalContact.email}>{legalContact.email}</a>. Nunca envie sua senha.</p>
}

const documents: Record<LegalKind, LegalDocument> = {
  cookies: {
    title: 'Política de cookies',
    introduction: 'Entenda o que o Gandalf guarda no seu navegador e como você pode controlar essas informações.',
    sections: [
      { id: 'cookies-e-armazenamento', title: 'Cookies e armazenamento no navegador', content: <>
        <p>Cookies são pequenos arquivos que um site pode guardar no navegador e receber em acessos posteriores. O armazenamento local (localStorage) também guarda informações no dispositivo, mas não as envia automaticamente em cada requisição.</p>
        <p>A aplicação Gandalf não define cookies próprios de autenticação, publicidade ou análise de audiência. A preferência de tema é guardada no armazenamento local. Os dados de acesso à conta ficam apenas na memória da página.</p>
      </> },
      { id: 'o-que-guardamos', title: 'O que fica no seu dispositivo', content: <dl className="legal-storage">
        <div><dt>Preferência de tema</dt><dd>A chave <code>gandalf-theme</code>, no localStorage, guarda somente a escolha entre claro e escuro. É uma preferência funcional, sem identificador de conta, e permanece até você limpar os dados do site. A aplicação grava a preferência ao carregar e ao trocar o tema.</dd></div>
        <div><dt>Sessão de acesso</dt><dd>Os tokens de acesso e renovação ficam na memória da página, sem cookies, localStorage ou sessionStorage. Recarregar ou fechar a página encerra a sessão no navegador. Para revogar o token de renovação no servidor, use a opção de sair da conta.</dd></div>
      </dl> },
      { id: 'servicos-externos', title: 'Conteúdo e sites externos', content: <>
        <p>Algumas capas são carregadas do Open Library. Nesses acessos, o provedor recebe informações técnicas da conexão, como o endereço IP. Ao abrir links para fontes, buscas ou plataformas de música e livros, você passa a navegar em outro site, que pode utilizar seus próprios cookies e políticas.</p>
        <p>O Gandalf não incorpora ferramentas de publicidade, pixels de marketing ou analytics. Caso essas tecnologias sejam adicionadas, esta política deverá ser atualizada e as escolhas aplicáveis apresentadas antes de ativar tecnologias opcionais.</p>
      </> },
      { id: 'como-controlar', title: 'Como controlar o armazenamento', content: <>
        <p>Você pode remover a preferência de tema em “Dados do site” ou “Armazenamento” nas configurações do navegador. Isso não exclui sua conta, seus favoritos ou suas playlists, que ficam no servidor. No próximo acesso, a aplicação volta ao tema escuro e grava novamente sua preferência.</p>
        <p>Para impedir novas gravações, bloqueie o armazenamento do site nas configurações do navegador. A preferência de tema pode deixar de ser lembrada. A leitura das políticas e a navegação pública devem continuar disponíveis mesmo com o armazenamento bloqueado.</p>
      </> },
      { id: 'contato', title: 'Contato e informações relacionadas', content: <>
        <Contact />
        <p>Leia também a <Link to="/politica-de-privacidade">Política de privacidade</Link> e o <a href={cookiesGuideUrl} target="_blank" rel="noopener noreferrer">guia de cookies da ANPD</a>.</p>
      </> },
    ],
  },
  privacy: {
    title: 'Política de privacidade',
    introduction: 'Saiba quais informações são utilizadas para recomendar músicas e livros, manter sua conta e guardar suas escolhas.',
    sections: [
      { id: 'responsavel', title: 'Quem é responsável pelos dados', content: <>
        <Contact />
        <p>Esta política se aplica ao Gandalf e descreve o tratamento de dados na aplicação. Você pode fazer buscas públicas sem criar uma conta.</p>
      </> },
      { id: 'dados-utilizados', title: 'Quais informações utilizamos', content: <ul>
        <li><strong>Conta:</strong> e-mail, nome de usuário, senha protegida por hash, identificador e datas de criação e atualização. A senha não é armazenada em texto aberto.</li>
        <li><strong>Buscas:</strong> o texto do pedido, filtros, referências, livro escolhido e opções de leitura são processados para produzir sugestões. Evite incluir dados sensíveis ou informações pessoais de outras pessoas nos campos livres.</li>
        <li><strong>Itens salvos:</strong> favoritos, nomes e descrições de playlists, faixas, ordem dos itens e datas de salvamento são associados à sua conta.</li>
        <li><strong>Operação e segurança:</strong> tokens de sessão e seus registros de renovação, endereço IP para limitar tentativas e dados técnicos de requisições e erros. A infraestrutura de hospedagem também pode registrar informações de conexão.</li>
        <li><strong>Preferência de interface:</strong> tema claro ou escuro guardado no dispositivo, conforme a <Link to="/politica-de-cookies">Política de cookies</Link>.</li>
      </ul> },
      { id: 'finalidades', title: 'Por que utilizamos os dados', content: <>
        <p>Usamos os dados necessários para atender seus pedidos, autenticar o acesso e guardar suas seleções, com fundamento na execução do serviço solicitado. Registros de segurança apoiam a prevenção de abuso, mediante avaliação de legítimo interesse. Obrigações legais e defesa de direitos podem exigir tratamento específico.</p>
        <p>Quando uma finalidade depender de consentimento, ele deverá ser solicitado separadamente e poderá ser revogado. Ler esta política ou aceitar os termos não autoriza, por si só, novos usos de dados.</p>
      </> },
      { id: 'compartilhamento', title: 'Provedores e compartilhamento', content: <>
        <p>A versão hospedada utiliza Vercel para servir a aplicação e Neon para o banco de dados. Esses provedores processam informações necessárias à hospedagem, ao armazenamento e à segurança. A infraestrutura contratada utiliza região em São Paulo; operações de suporte e serviços de terceiros podem envolver processamento em outros países, sujeito às exigências legais aplicáveis.</p>
        <p>As integrações de catálogo consultam Open Library e MusicBrainz com termos de busca e referências necessários à consulta. Capas externas são carregadas pelo navegador. Links externos levam a serviços com políticas próprias.</p>
        <p>A integração opcional com Groq, quando configurada e habilitada, pode receber o texto do pedido e metadados de catálogo para interpretar e classificar sugestões. O fluxo de recomendação não envia e-mail, senha ou tokens de conta ao provedor de IA. A publicação de outubro de 2026 foi configurada com a IA desabilitada; sua ativação exige revisar este aviso e as condições do provedor antes do uso.</p>
        <p>Não há integração de publicidade ou venda de dados na aplicação. Informações também podem ser fornecidas em cumprimento de obrigação legal ou determinação válida de autoridade competente.</p>
      </> },
      { id: 'conservacao', title: 'Armazenamento e conservação', content: <>
        <p>Conta, favoritos e playlists permanecem no banco enquanto forem necessários à manutenção da conta e do serviço. Você pode remover favoritos e playlists pela interface; para solicitar a exclusão da conta ou outros dados, utilize o e-mail de contato. A interface ainda não possui exclusão automática de conta.</p>
        <p>Os resultados temporários usados para explicar e salvar sugestões expiram após uma hora e podem ser removidos antes pelo limite de cache. Esse cache guarda itens e metadados da seleção, sem o texto do pedido ou vínculo com a conta. Outros caches de consulta seguem os prazos configurados para cada provedor.</p>
        <p>Expirar um token ou um cache não garante a remoção imediata de todos os registros físicos. Logs, registros de segurança e eventuais cópias de segurança seguem as necessidades operacionais e os prazos dos provedores; não foi definido um prazo único para essas categorias. Informaremos os critérios aplicáveis mediante solicitação, incluindo retenções exigidas por lei.</p>
      </> },
      { id: 'direitos', title: 'Seus direitos e como exercê-los', content: <>
        <p>Nos casos previstos pela LGPD, você pode pedir confirmação e acesso, correção, informação sobre compartilhamento, portabilidade, anonimização, bloqueio ou eliminação, além de revogar consentimento ou contestar tratamento irregular. Pode também solicitar revisão de decisões exclusivamente automatizadas que afetem seus interesses e procurar a ANPD.</p>
        <p>Envie sua solicitação ao contato indicado nesta página, preferencialmente pelo e-mail da conta. Podemos pedir informações proporcionais para confirmar sua identidade, sem solicitar sua senha. O pedido será analisado conforme a legislação e as exceções de conservação aplicáveis.</p>
        <p>As sugestões organizam músicas e livros a partir do pedido e dos filtros; podem conter erros e não produzem, por si só, decisões de crédito, emprego ou acesso a direitos.</p>
      </> },
      { id: 'seguranca-e-menores', title: 'Segurança e proteção de menores', content: <>
        <p>O projeto utiliza senha protegida por hash, tokens com validade e controles de acesso para separar dados entre contas. A versão pública utiliza HTTPS. Nenhuma medida elimina todos os riscos: proteja sua senha, saia da conta em dispositivos compartilhados e comunique suspeitas pelo e-mail de contato.</p>
        <p>O Gandalf não oferece um fluxo específico de cadastro infantil. Caso um responsável identifique dados de uma criança na aplicação, pode entrar em contato para análise e providências adequadas, observando o melhor interesse da criança ou adolescente.</p>
      </> },
      { id: 'atualizacoes', title: 'Atualizações e referência legal', content: <>
        <p>Alterações no funcionamento ou nas finalidades de tratamento serão refletidas nesta página, com a data de atualização. Mudanças que exijam informação adicional ou consentimento deverão ser apresentadas antes do novo tratamento.</p>
        <p>Referência: <a href={lgpdUrl} target="_blank" rel="noopener noreferrer">Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018)</a>. Consulte também os <Link to="/termos-de-uso">Termos de uso</Link>.</p>
      </> },
    ],
  },
  terms: {
    title: 'Termos de uso',
    introduction: 'As condições para explorar o Gandalf, criar uma conta e salvar músicas, livros e trilhas de leitura.',
    sections: [
      { id: 'servico', title: 'Sobre o serviço', content: <>
        <p>O Gandalf é um projeto de descoberta de músicas e livros a partir de descrições, referências e filtros. Também permite criar seleções musicais para acompanhar uma leitura. O serviço é disponibilizado por {legalContact.name}.</p>
        <p>As buscas públicas podem ser utilizadas sem conta. Uma conta permite salvar favoritos e playlists. O Gandalf não reproduz áudio, distribui livros nem vende os conteúdos recomendados; os links levam a fontes e plataformas externas.</p>
      </> },
      { id: 'uso-e-conta', title: 'Uso e responsabilidade pela conta', content: <>
        <p>Ao utilizar o serviço, observe estes termos e a legislação aplicável. No cadastro, a ação de criar a conta é acompanhada de links para estes termos e para a política de privacidade, para que você possa consultá-los antes de prosseguir.</p>
        <p>Forneça informações corretas, mantenha a senha protegida e utilize apenas contas às quais tenha acesso autorizado. A sessão no navegador termina ao recarregar ou fechar a página; use “Sair” para solicitar também a revogação da renovação no servidor.</p>
        <p>Se você precisar de representação ou assistência legal para utilizar o serviço, o uso deve ocorrer com a participação do responsável. A aplicação não possui verificação de idade ou um fluxo dedicado a crianças.</p>
      </> },
      { id: 'uso-permitido', title: 'Uso responsável', content: <ul>
        <li>Não tente acessar dados de outras contas, contornar controles de segurança ou explorar falhas sem autorização.</li>
        <li>Não utilize automação abusiva, sobrecarga deliberada, spam ou métodos para contornar limites de requisição.</li>
        <li>Não envie conteúdo ilícito, dados de terceiros sem autorização ou material que viole direitos autorais e outros direitos.</li>
        <li>Respeite as condições das fontes e plataformas acessadas por links externos.</li>
      </ul> },
      { id: 'recomendacoes', title: 'Recomendações e conteúdo de terceiros', content: <>
        <p>As recomendações dependem dos catálogos disponíveis, regras de classificação e, quando habilitada, inteligência artificial. Resultados, explicações, capas, durações e metadados podem estar incompletos, desatualizados ou incorretos. Confira as informações na fonte antes de tomar uma decisão ou contratar um serviço externo.</p>
        <p>Títulos, obras, músicas, imagens e marcas pertencem aos respectivos titulares. A exibição de metadados e links não transfere direitos sobre esses conteúdos nem indica vínculo oficial, patrocínio ou endosso. O nome Gandalf é utilizado neste projeto sem alegação de afiliação com titulares de obras ou marcas de terceiros.</p>
        <p>Plataformas externas podem exigir conta, pagamento ou condições próprias. O Gandalf não controla sua disponibilidade, preços ou tratamento de dados.</p>
      </> },
      { id: 'disponibilidade', title: 'Disponibilidade e limites', content: <>
        <p>O serviço pode passar por manutenção, alterações e interrupções, inclusive por limites de provedores externos. Não há garantia de disponibilidade contínua ou de que cada busca encontrará resultados.</p>
        <p>Medidas proporcionais de limitação ou suspensão podem ser adotadas para proteger o serviço contra abuso e cumprir a lei. Essas condições não afastam responsabilidades legais nem direitos que não possam ser limitados pela legislação, incluindo direitos do consumidor quando aplicáveis.</p>
      </> },
      { id: 'dados-e-encerramento', title: 'Dados e encerramento do uso', content: <>
        <p>O tratamento de dados está descrito na <Link to="/politica-de-privacidade">Política de privacidade</Link> e o armazenamento no navegador na <Link to="/politica-de-cookies">Política de cookies</Link>. O uso do serviço não representa consentimento geral para publicidade ou novas finalidades de tratamento.</p>
        <p>Você pode deixar de utilizar o Gandalf a qualquer momento e remover favoritos e playlists pela interface. Solicitações de exclusão da conta e outras demandas sobre dados devem ser enviadas ao contato abaixo, pois ainda não há exclusão automática de conta na interface.</p>
      </> },
      { id: 'alteracoes-e-contato', title: 'Alterações, legislação e contato', content: <>
        <p>Estes termos podem ser atualizados para refletir mudanças no serviço. A data da versão aparece no início desta página. Alterações relevantes deverão ser comunicadas de forma acessível, e não retiram direitos adquiridos ou garantias legais. Aplica-se a legislação brasileira, preservadas as regras legais de competência e os direitos do usuário.</p>
        <Contact />
      </> },
    ],
  },
}

export default function Legal({ kind }: { kind: LegalKind }) {
  const documentContent = documents[kind]
  const heading = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    const previousTitle = document.title
    document.title = documentContent.title + ' | Gandalf'
    heading.current?.focus({ preventScroll: true })
    return () => { document.title = previousTitle }
  }, [documentContent.title])

  return <div className="legal-page container">
    <Link className="legal-back" to="/"><ArrowLeft size={17} aria-hidden="true" /> Voltar ao início</Link>
    <header className="legal-header">
      <h1 ref={heading} tabIndex={-1}>{documentContent.title}</h1>
      <p>{documentContent.introduction}</p>
      <p className="legal-updated">Última atualização: <time dateTime={legalUpdatedAt}>10 de outubro de 2026</time></p>
    </header>
    <div className="legal-layout">
      <aside className="legal-sidebar">
        <nav className="legal-documents" aria-label="Documentos legais">
          {legalLinks.map(link => <NavLink key={link.kind} to={link.to} className={({ isActive }) => isActive ? 'is-active' : undefined}>{link.label}</NavLink>)}
        </nav>
        <nav className="legal-index" aria-label="Nesta página">
          <h2>Nesta página</h2>
          <ul>{documentContent.sections.map(section => <li key={section.id}><a href={'#' + section.id}>{section.title}</a></li>)}</ul>
        </nav>
      </aside>
      <article className="legal-content" aria-label={documentContent.title}>
        {documentContent.sections.map(section => <section key={section.id} id={section.id} aria-labelledby={'heading-' + section.id}>
          <h2 id={'heading-' + section.id}>{section.title}</h2>
          {section.content}
        </section>)}
      </article>
    </div>
  </div>
}
