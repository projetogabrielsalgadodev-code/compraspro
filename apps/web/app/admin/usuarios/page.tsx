import { getUsers } from "./actions";
import { UserManager } from "./components/user-manager";

export default async function UsuariosPage() {
  const users = await getUsers();

  return (
    <div className="p-8 h-full flex flex-col space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-texto">Usuários</h2>
        <p className="text-mutedtext">
          Gerencie os permissionamentos, contatos e funções de quem acessa o painel.
        </p>
      </div>

      <UserManager initialUsers={users} />
    </div>
  );
}
