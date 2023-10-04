<?php
namespace Rugaard\OAuth2\Client\Netatmo\Provider;

use League\OAuth2\Client\Provider\AbstractProvider;
use League\OAuth2\Client\Provider\Exception\IdentityProviderException;
use League\OAuth2\Client\Token\AccessToken;
use Psr\Http\Message\ResponseInterface;

/**
 * Class Netatmo
 *
 * @package Rugaard\OAuth2\Client\Netatmo\Provider
 */
class Netatmo extends AbstractProvider
{
    /**
     * Returns the base URL for authorizing a client.
     *
     * @return string
     */
    public function getBaseAuthorizationUrl()
    {
        return 'https://api.netatmo.net/oauth2/authorize';
    }

    /**
     * Returns authorization parameters based on provided options.
     *
     * @param  array $options
     * @return array
     */
    protected function getAuthorizationParameters(array $options)
    {
        $parameters = parent::getAuthorizationParameters($options);

        // If the "read_thermostat" scope is not found in the scope list,
        // we need to append it, since it's required to retrieve user details.
        if (strpos($parameters['scope'], 'read_thermostat') === false) {
            $parameters['scope'] .= ' read_thermostat';
        }

        return $parameters;
    }

    /**
     * Returns the base URL for requesting an access token.
     *
     * @param  array $params
     * @return string
     */
    public function getBaseAccessTokenUrl(array $params)
    {
        return 'https://api.netatmo.net/oauth2/token';
    }

    /**
     * Returns the default scopes used by this provider.
     *
     * @return array|string
     */
    protected function getDefaultScopes()
    {
        return ['read_thermostat'];
    }

    /**
     * Returns the string that should be used to separate scopes when building
     * the URL for requesting an access token.
     *
     * @return string
     */
    public function getScopeSeparator()
    {
        return ' ';
    }

    /**
     * Checks a provider response for errors.
     *
     * @param  \Psr\Http\Message\ResponseInterface $response
     * @param  array|string                        $data
     * @return void
     * @throws \League\OAuth2\Client\Provider\Exception\IdentityProviderException
     */
    protected function checkResponse(ResponseInterface $response, $data)
    {
        if ($response->getStatusCode() >= 400) {
            throw new IdentityProviderException(
                !empty($data['message']) ? $data['message'] : $response->getReasonPhrase(),
                $response->getStatusCode(),
                $data
            );
        }
    }

    /**
     * Returns the URL for requesting the resource owner's details.
     *
     * @param  \League\OAuth2\Client\Token\AccessToken $token
     * @return string
     */
    public function getResourceOwnerDetailsUrl(AccessToken $token)
    {
        return 'https://api.netatmo.com/api/homesdata?access_token=' . $token;
    }

    /**
     * Generates a resource owner object from a successful resource owner
     * details request.
     *
     * @param  array $response
     * @param  AccessToken $token
     * @return \League\OAuth2\Client\Provider\ResourceOwnerInterface
     */
    protected function createResourceOwner(array $response, AccessToken $token)
    {
        return new NetatmoResourceOwner($response['body']['user']);
    }
}