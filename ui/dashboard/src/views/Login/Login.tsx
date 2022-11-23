import React, { useState } from 'react';
import { useLogin } from 'archilyse-ui-components';
import { C } from '../../common';
import { ActionsType, checkAccess } from '../../common/roles';
import getInitialPageUrlByRole from '../../common/modules/getInitialPageUrlByRole';
import './login.scss';

const Login = () => {
  const [user, setUser] = useState('');
  const [password, setPassword] = useState('');

  const { handleSubmit } = useLogin({
    getInitialPageUrl: getInitialPageUrlByRole,
    checkAccess: intent => checkAccess(intent as ActionsType),
  });

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    handleSubmit({ user, password });
  };

  const Greeting = () => {
    return (
      <div className="greeting">
        <h1>
          Welcome to <br />
          Archilyse.
        </h1>
        <h1 className="subtitle">Please sign in.</h1>
      </div>
    );
  };

  return (
    <div className="login">
      <Greeting />
      <form onSubmit={onSubmit}>
        <input
          id="user"
          name="user"
          placeholder="Username"
          className="login-input"
          required
          onChange={event => setUser(event.target.value)}
          value={user}
        />
        <input
          id="password"
          name="password"
          placeholder="Password"
          className="login-input"
          type="password"
          required
          onChange={event => setPassword(event.target.value)}
          value={password}
        />
        <button type="submit" className="secondary-button extra-large">
          Sign in
        </button>
        <a href={C.URLS.ARCHILYSE_CONTACT()} target="_blank" rel="noreferrer">
          Get in contact
        </a>
      </form>
    </div>
  );
};
export default Login;
